import CoolProp.CoolProp as CP
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from math import ceil, floor
from typing import Tuple
import pandas as pd
import os

st.set_page_config(page_title="Onboard Mass", layout="wide")

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

class RP1Properties:

    def __init__(self):
        # Constantes pour le RP-1
        self.M = 170.0  # Masse molaire approximative (g/mol)
        self.Tc = 683.0  # Température critique (K)
        self.Pc = 21.0e5  # Pression critique (Pa)
        self.T_triple = 240.0  # Température du point triple (K)
        self.P_triple = 1e-6  # Pression du point triple (Pa)
        self.T_melting_ref = 233.0  # Température de fusion à pression atmosphérique (K)
        self.JT_inversion_temp = 700.0  # Température d'inversion Joule-Thomson approx. (K)

    def density(self, T, P):
        """Densité du RP-1 en fonction de la température et de la pression."""
        # Densité approximative à 293.15K est 820 kg/m³
        # Correction en fonction de la température
        rho_ref = 820.0
        thermal_expansion = 0.001  # Coefficient d'expansion thermique approximatif (1/K)
        compressibility = 5e-10  # Coefficient de compressibilité approximatif (1/Pa)
        
        # Correction pour la température et la pression
        rho = rho_ref * (1 - thermal_expansion * (T - 293.15)) * (1 + compressibility * (P - 1.01325e5))
        return rho

    def specific_heat(self, T):
        """Capacité thermique spécifique du RP-1."""
        # Valeur approximative à température ambiante (J/kg·K)
        cp_ref = 2000.0
        # Variation avec température
        cp = cp_ref + 2.5 * (T - 293.15)
        return cp
    
    def enthalpy(self, T, P):
        """Enthalpie du RP-1 (kJ/kg)."""
        # Valeur approximative, basée sur la capacité thermique
        h_ref = 0.0  # Référence à 293.15K
        h = h_ref + self.specific_heat(T) * (T - 293.15) / 1000.0
        return h
    
    def thermal_expansion_coeff(self, T):
        """Coefficient d'expansion thermique (1/K)."""
        return 0.001  # Valeur approximative
    
    def viscosity(self, T):
        """Viscosité du RP-1 (Pa·s)."""
        # Viscosité du RP-1 (approximation)
        mu_ref = 0.0021  # à 293.15K (Pa·s)
        # Modèle d'Arrhenius simplifié pour la dépendance en température
        E_a = 20000.0  # Énergie d'activation (J/mol)
        R = 8.314  # Constante des gaz parfaits (J/mol·K)
        mu = mu_ref * np.exp(E_a/R * (1/T - 1/293.15))
        return mu
    
    def thermal_conductivity(self, T):
        """Conductivité thermique du RP-1 (W/m·K)."""
        # Valeur approximative
        k_ref = 0.145  # à 293.15K
        k = k_ref * (1 - 0.0005 * (T - 293.15))
        return k
    
    def vapor_pressure(self, T):
        """
        # Constantes d'Antoine pour le n-décane (valable entre ~150 K et 450 K)
        A = 6.90565
        B = 1265.67
        C = 222.65
        # Formule d'Antoine (résultat en mmHg)
        log10_P_mmHg = A - (B / (C + (T - 273.15)))
        P_mmHg = 10 ** log10_P_mmHg
    
        # Conversion mmHg → Pa (1 mmHg ≈ 133.322 Pa)
        P_Pa = P_mmHg * 133.322
        return P_Pa * 1e-5
        """
        # Constantes ajustées pour le RP-1 (basées sur des données réelles)
        A = 1.2e8  # Constante ajustée
        B = 1900  # Constante ajustée pour correspondre à la température d'ébullition
        T_0 = 232  # Température de référence en Kelvin 
        P = A * np.exp(-B / (T - T_0))
        return P * 1e-5
    
    def get_phase(self, T, P):
        """Détermine la phase du RP-1."""
        if T < self.get_melting_temperature(P * 1e-5):
            return "solid"
        elif P > self.Pc and T > self.Tc:
            return "supercritical"
        elif P > self.Pc:
            return "supercritical_liquid"
        elif T > self.Tc:
            return "supercritical_gas"
        else:
            # Sous Tc et sous Pc → on regarde la pression de vapeur
            Pvap = self.vapor_pressure(T) * 1e5
            if P < Pvap:
                return "gas"
            else:
                return "liquid"
    
    def get_melting_temperature(self, P_bar):
        """Température de fusion du RP-1 en fonction de la pression (bar)."""
        # Modèle simplifié: la température de fusion augmente légèrement avec la pression
        P_Pa = P_bar * 1e5
        T_melt = self.T_melting_ref * (1 + 2e-10 * (P_Pa - 1.01325e5))
        return T_melt
    
    def get_JT_inversion_temp(self):
        """Température d'inversion Joule-Thomson du RP-1."""
        return self.JT_inversion_temp

def ceil_decimals(value, decimals):
    factor = 10 ** decimals
    return ceil(value * factor) / factor

def floor_decimal(value, decimals):
    factor = 10 ** decimals
    return floor(value * factor) / factor

def get_phase_temp_limits(fluid: str, quality: float = 0, step: float = 0.001) -> Tuple[float, float]:

    Tc = CP.PropsSI("T_critical", fluid)
    T_triple = CP.PropsSI("T_triple", fluid)
    T_test_min = T_triple - 1.0
    T_test_max = Tc + 1.0
    state = CP.AbstractState('HEOS', fluid)
    p_triple = state.keyed_output(CP.iP_triple)  

    if fluid in ['N2', 'O2']:
        return T_triple, Tc
    else:
        if fluid == 'He':
            T_min = lambda_transition_temperature(p_triple * 1e-5)
        else:  
            while True: 
                try:
                    CP.PropsSI("P", "T", T_test_min, "Q", quality, fluid)
                    T_min = T_test_min
                    break
                except:
                    T_test_min += step
        while True: 
            try:
                CP.PropsSI("P", "T", T_test_max, "Q", quality, fluid)
                T_max = T_test_max
                break
            except:
                T_test_max -= step
                
        try:
            CP.PropsSI("P", "T", T_min, "Q", quality, fluid)
            CP.PropsSI("P", "T", T_max, "Q", quality, fluid)
        except ValueError as e:
            raise ValueError(f"Erreur lors de la vérification finale : {str(e)}")
        
        return ceil_decimals(T_min, 2), floor_decimal(T_max, 2)

def melting_temperature_H2(pressure_bar):
    pressure_GPa = pressure_bar / 1e4  
    T_melt = 13.857 * (1 + pressure_GPa / 0.0286) ** 0.589 * np.exp(-4.6e-3 * pressure_GPa)
    return T_melt

def nitrogen_melting_temperature(p):
    t_t = 63.19
    p_t = 0
    a = 5500
    c = 0.565
    T = t_t / ((1 - (p - p_t) / a) ** (1/c))
    return T

def helium_melting_temperature(pressure_bar):
    p_min = 25.3
    if pressure_bar < p_min:
        T = 0
    else:
        T = 1.0 + ((pressure_bar - 25.3) / 1.72) ** (1 / 2.89)
    return T

def lambda_transition_temperature(P):
    return 2.17 + 0.012 * P - 0.0003 * P ** 2

def get_melting_temperature(fluid, pressure_bar):
    try:
        if fluid == "H2":
            return melting_temperature_H2(pressure_bar)
        elif fluid == 'N2':
            return nitrogen_melting_temperature(pressure_bar)
        elif fluid == 'He':
            return helium_melting_temperature(pressure_bar)
        state = CP.AbstractState("HEOS", fluid)
        pressure_pa = pressure_bar * 1e5
        temp_melt = state.melting_line(CP.iT, CP.iP, pressure_pa)
        if fluid == 'O2':
            return temp_melt + 0.01
        else:
            return temp_melt
    except ValueError:
        st.write(f"⚠️ Impossible de récupérer la température de fusion pour {fluid} à {pressure_bar} bar.")
        return None
    
#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)

#st.sidebar.image(logo_path)
#st.image('ESA_logo_2020_Deep.png')

st.write(f"### Onboard Mass Calculation Tool")
st.write(f'Selected normalization conditions : **1 bar / 288.15 K (15°C)**')
fluide = st.selectbox("Select the fluid", ['H2O', 'H2','N2', 'O2', 'He', 'CH4', 'RP-1'])
P_calc = st.number_input("Pressure (bar)", min_value=0.0, value=1.0)
T_calc = st.number_input("Temperature (K)", min_value=1.0, value=300.0)
V = st.number_input("Volume (m³)", min_value=0.0, value=1.0)
NV = V * (P_calc/ 1 ) * (288.15 / ((T_calc - 288.15) + 288.15))
if fluide == "RP-1":
    rp1 = RP1Properties()
    p_triple_calc = rp1.P_triple
    phase_calc = rp1.get_phase(P_calc * 1e5, T_calc)
    temp_melt_calc = rp1.get_melting_temperature(P_calc)
    
else:
    state_calc = CP.AbstractState('HEOS', fluide)
    p_triple_calc = state_calc.keyed_output(CP.iP_triple)
    t_min_phase_calc, t_max_phase_calc = get_phase_temp_limits(fluide)
    temp_melt_calc = get_melting_temperature(fluide, P_calc)
    phase_calc = CP.PhaseSI('P', P_calc * 1e5, 'T', T_calc, fluide)

if phase_calc in ['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'supercritical'] and T_calc >= temp_melt_calc:  
    if fluide == 'RP-1':
        rho = rp1.density(T_calc, P_calc * 1e5)
    else:
        rho = CP.PropsSI('D', 'T', T_calc, 'P', P_calc * 1e5, fluide)
    mass = rho * V * 1e3
    if (mass / 1000) >= 1:
        #st.write(f'Density used : {rho:.2f} kg/m³')
        st.write(f'Onboard mass : {mass * 1e-3:.2f} kg')
        st.write(f'Normalized volume : {NV:.2f} Nm³')
    else:
        #st.write(f'Density used : {rho:.2f} kg/m³')
        st.write(f'Onboard mass : {mass:.2f} g')
        st.write(f'Normalized volume : {NV:.2f} Nm³')
else:
    st.write(f'**{fluide}** is in the **solid** phase')
    st.write(f'**Minimal temperature to return to liquid phase :** {ceil_decimals(temp_melt_calc, 2)} K')




