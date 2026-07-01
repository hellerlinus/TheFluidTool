import CoolProp.CoolProp as CP
import streamlit as st
import numpy as np
from math import ceil, floor
from typing import Tuple
import os
from rocketprops.rocket_prop import get_prop

st.set_page_config(page_title="Characteristics", layout="wide")

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

def convert_temp_K_to_R(temp_K):
    """Convertit la température de Kelvin à Rankine"""
    return temp_K * 9/5

def convert_temp_R_to_K(temp_R):
    """Convertit la température de Rankine à Kelvin"""
    return temp_R * 5/9

def convert_psia_to_pa(psia):
    """Convertit la pression de psia à Pascal"""
    return psia * 6894.76

def convert_pa_to_psia(pa):
    """Convertit la pression de Pascal à psia"""
    return pa / 6894.76

def sgml_to_kgm3(sg):
    """Convertit la densité de g/ml à kg/m³"""
    return sg * 1000

def poise_to_pa_s(poise):
    """Convertit la viscosité de poise à Pa·s"""
    return poise / 10

def btu_lbm_r_to_j_kg_k(cp):
    """Convertit la capacité thermique de BTU/lbm-R à J/kg-K"""
    return cp * 4186.8

def btu_hr_ft_r_to_w_m_k(k):
    """Convertit la conductivité thermique de BTU/hr-ft-R à W/m-K"""
    return k * 1.73073

def btu_lbm_to_j_kg(btu_lbm):
    """Convertit BTU/lbm en J/kg"""
    return btu_lbm * 2326.0

def format_number(x, precision=2):
    if x is None:
        return "N/A"
    if isinstance(x, (int, float)):
        if abs(x - int(x)) < 1e-6:
            return f"{int(x)}"
        else:
            return f"{x:.{precision}f}"
    return str(x)

class RP1Properties:

    def __init__(self):
        RP1 = get_prop('RP-1')
        self.M = 170.0
        self.Tc = convert_temp_R_to_K(RP1.Tc)  # Température critique en K
        self.Pc = convert_psia_to_pa(RP1.Pc)  # Pression critique en Pa
        self.T_triple = 240.0  # Estimation
        self.P_triple = 1e-6   # Estimation
        self.T_melting_ref = 233.0  # Estimation
        self.JT_inversion_temp = 700.0  # Approximatif

    def density(self, T, P):
        RP1 = get_prop('RP-1')
        T_degR = convert_temp_K_to_R(T)
        P_psia = convert_pa_to_psia(P)
        sg = RP1.SG_compressed(T_degR, P_psia)
        rho = sgml_to_kgm3(sg)
        return rho

    def specific_heat(self, T):
        RP1 = get_prop('RP-1')
        T_degR = convert_temp_K_to_R(T)
        cp_btu = RP1.CpAtTdegR(T_degR)
        cp = btu_lbm_r_to_j_kg_k(cp_btu)
        return cp
    
    def enthalpy(self, T, P):
        """
        Calcule l'enthalpie du RP-1 à une température et pression données.
        
        Cette fonction utilise l'intégration numérique de la capacité thermique (Cp) 
        depuis une température de référence, puis ajoute la correction pour la pression.
        
        Args:
            T_K: Température en Kelvin
            P_Pa: Pression en Pascal
            T_ref_K: Température de référence en Kelvin (défaut: 273.15K)
            
        Returns:
            enthalpie en J/kg
        """
        RP1 = get_prop('RP-1')
        T_ref = 298.15
        P_psia = convert_pa_to_psia(P)
        
        # 1. Calculer l'enthalpie à la pression de saturation par intégration de Cp
        # Diviser l'intervalle de température en plusieurs petits pas
        num_steps = 100
        T_range = np.linspace(T_ref, T, num_steps + 1)
        dT = (T - T_ref) / num_steps
        
        # Enthalpie au point de référence (considérée comme zéro à T_ref)
        h_ref = 0.0
        
        # Intégration numérique de Cp pour obtenir l'enthalpie
        h_sat = h_ref
        for i in range(num_steps):
            T_mid_K = 0.5 * (T_range[i] + T_range[i+1])
            T_mid_R = convert_temp_K_to_R(T_mid_K)
            
            # Obtenir Cp à cette température
            cp_btu = RP1.CpAtTdegR(T_mid_R)
            cp_j = btu_lbm_r_to_j_kg_k(cp_btu)
            
            # Intégrer: dh = Cp * dT
            dh = cp_j * dT
            h_sat += dh
        
        # 2. Ajouter la correction pour la pression (enthalpie de fluide comprimé)
        # Pour un liquide presque incompressible, on peut utiliser l'approximation:
        # h(T,P) = h(T,Psat) + v * (P - Psat) * [1 - 0.5 * β * (T - Tref)]
        # où v = 1/ρ est le volume spécifique, β est le coefficient de dilatation thermique
        
        # Calculer la pression de saturation à cette température
        T_R = convert_temp_K_to_R(T)
        P_sat_psia = RP1.PvapAtTdegR(T_R)
        P_sat_Pa = P_sat_psia * 6894.76
        
        # Si la pression est inférieure à la pression de saturation, le fluide est gazeux
        # et cette approximation n'est pas valide
        if P < P_sat_Pa:
            print(f"Attention: À {T} K, la pression {P/1000:.2f} kPa est inférieure à la pression de saturation {P_sat_Pa/1000:.2f} kPa.")
            print("Le RP-1 est en phase gazeuse, et le calcul d'enthalpie est moins précis.")
            # On peut ajouter la chaleur latente de vaporisation si nécessaire
            try:
                hvap_btu = RP1.HvapAtTdegR(T_R)
                hvap_j = btu_lbm_to_j_kg(hvap_btu)
                h_sat += hvap_j
            except:
                print("Chaleur latente de vaporisation non disponible.")
        
        # Pour la phase liquide, appliquer la correction de pression
        elif P > P_sat_Pa:
            # Obtenir la densité et calculer le volume spécifique
            sg = RP1.SG_compressed(T_R, P_psia)
            rho = sg * 1000  # kg/m³
            v = 1 / rho  # m³/kg
            
            # Estimer le coefficient de dilatation thermique
            delta_T = 1.0  # 1 K
            T_plus_R = convert_temp_K_to_R(T + delta_T)
            sg_plus = RP1.SG_compressed(T_plus_R, P_psia)
            rho_plus = sg_plus * 1000
            beta = -(1/rho) * ((rho_plus - rho)/delta_T)  # 1/K
            
            # Correction d'enthalpie pour la pression
            h_correction = v * (P - P_sat_Pa) * (1 - 0.5 * beta * (T - T_ref))
            h_sat += h_correction
        
        return h_sat
 
    def thermal_expansion_coeff(self, T, P):
        RP1 = get_prop('RP-1')
        T_degR = convert_temp_K_to_R(T)
        P_psia = convert_pa_to_psia(P)
        delta_T = 1.0
        sg_plus = RP1.SG_compressed(T_degR + convert_temp_K_to_R(delta_T), P_psia)
        rho_plus = sgml_to_kgm3(sg_plus)
        beta = -(1/self.density(T, P)) * ((rho_plus - self.density(T, P))/delta_T)
        return beta
    
    def viscosity(self, T, P):
        RP1 = get_prop('RP-1')
        T_degR = convert_temp_K_to_R(T)
        P_psia = convert_pa_to_psia(P)
        mu_poise = RP1.Visc_compressed(T_degR, P_psia)
        mu = poise_to_pa_s(mu_poise)
        return mu
    
    def thermal_conductivity(self, T):
        RP1 = get_prop('RP-1')
        T_degR = convert_temp_K_to_R(T)
        k_btu = RP1.CondAtTdegR(T_degR)
        k = btu_hr_ft_r_to_w_m_k(k_btu)
        return k
    
    def vapor_pressure(self, T):
        RP1 = get_prop('RP-1')
        T_degR = convert_temp_K_to_R(T)
        vp_psia = RP1.PvapAtTdegR(T_degR)
        vp = convert_psia_to_pa(vp_psia)
        return vp * 1e-5
    
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

    if fluid == "RP-1":
        rp1 = RP1Properties()
        return rp1.T_triple, rp1.Tc

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
        if fluid == 'RP-1':
            rp1 = RP1Properties()
            return rp1.get_melting_temperature(pressure_bar)
        elif fluid == "H2":
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

def calculer_temperature_inversion_JT(fluid, P, T, nb_points=50):
    """
    Calcule la température d'inversion de Joule-Thomson pour un fluide donné à une pression spécifique.
    
    Arguments:
        fluide (str): Nom du fluide dans CoolProp (ex: 'Nitrogen', 'R134a', 'CO2')
        P (float): Pression en Pa
        T_range (tuple): Plage de température (min, max) en K
        nb_points (int): Nombre de points pour la discrétisation
    
    Returns:
        float: Température d'inversion en K ou None si non trouvée
    """
    if fluid == "RP-1":
        rp1 = RP1Properties()
        return rp1.get_JT_inversion_temp()
    elif fluid == 'H2O':
        T_critique = 647.1  # Température critique de l'eau en K
        P_critique = 22.06e6  # Pression critique de l'eau en Pa
        
        # Calcul amélioré de la température d'inversion Joule-Thomson
        T_JT = T_critique * (1 - (P * 1e-5 / P_critique))
        return T_JT
    else:
        temperatures = np.linspace(T, 1000, nb_points)
        
        mu_JT_prev = None
        T_prev = None
        T_inv = None
        
        for T in temperatures:
            try:
                # Calcul du coefficient de Joule-Thomson
                # μ_JT = (∂T/∂P)_H = -1/Cp * (T * (∂v/∂T)_P - v)
                
                # Calcul de la capacité thermique à pression constante
                Cp = CP.PropsSI('CPMASS', 'T', T, 'P', P, fluid)
                
                # Volume spécifique et sa dérivée par rapport à T à P constante
                v = 1.0 / CP.PropsSI('D', 'T', T, 'P', P, fluid)
                
                # Pour calculer la dérivée, on utilise une approximation par différence finie
                delta_T = 0.1  # Petit incrément de température
                v_plus = 1.0 / CP.PropsSI('D', 'T', T + delta_T, 'P', P, fluid)
                
                dv_dT = (v_plus - v) / delta_T
                
                # Coefficient de Joule-Thomson
                mu_JT = -1.0 / Cp * (T * dv_dT - v)
                
                # Si mu_JT change de signe, on a une température d'inversion
                if mu_JT_prev is not None and mu_JT * mu_JT_prev <= 0:
                    # Interpolation linéaire pour trouver la température d'inversion précise
                    T_inversion_estimee = T_prev + (T - T_prev) * abs(mu_JT_prev) / (abs(mu_JT_prev) + abs(mu_JT))
                    T_inv = T_inversion_estimee
                    break
                
                mu_JT_prev = mu_JT
                T_prev = T
                
            except Exception as e:
                # Certains points peuvent être hors des limites du modèle thermodynamique
                continue
        
        return T_inv

fluids = ['H2O', 'N2', 'O2', 'He', 'CH4', 'H2', 'RP-1']




st.title(f'Fluid Properties Calculator')

col1, col2 = st.columns([3, 1])

with col2:
    fluid = st.selectbox('Select fluid : ', fluids)

    if fluid == "RP-1":
        rp1 = RP1Properties()
        pc = rp1.Pc
        pmax = 50e6  # 500 bar max pour RP-1
        p_triple = rp1.P_triple
        t_min_phase, t_max_phase = get_phase_temp_limits(fluid)
        R = 8.314 / rp1.M * 1000  # Constante des gaz spécifique (J/kg.K)
    else:
        state = CP.AbstractState('HEOS', fluid)
        pc = state.keyed_output(CP.iP_critical)
        pmax = state.keyed_output(CP.iP_max)
        p_triple = state.keyed_output(CP.iP_triple)
        t_min_phase, t_max_phase = get_phase_temp_limits(fluid)
        R = CP.PropsSI("GAS_CONSTANT", fluid) / CP.PropsSI("M", fluid)

    pressure = st.number_input("Enter pressure (bar) : ", min_value = 0.001, max_value = 1000.0, value = 1.0, step = 0.1)
    temp_melt = get_melting_temperature(fluid, pressure)
    pressure_pa = pressure * 1e5
    temp = st.number_input("Enter temperature (K) : ", min_value = 0.0, max_value = 1000.0, value = 300.0)
    T_inversion = calculer_temperature_inversion_JT(fluid, pressure_pa, t_max_phase)

with col1:
    try :
        if fluid == 'He' and temp < lambda_transition_temperature(pressure) and pressure < 25.3:
            st.markdown(f'### Properties of {fluid} at {format_number(temp)} K and {format_number(pressure)} bar :')
            st.write(f'**{fluid}** is in the superfluid phase')
            st.write(f'**Minimal temperature to return to liquid phase :** {ceil_decimals(lambda_transition_temperature(pressure), 2)} K')
        else:
            if fluid == "RP-1":
                rp1 = RP1Properties()
                phase = rp1.get_phase(temp, pressure_pa)
            else:            
                phase = CP.PhaseSI('P', pressure_pa, 'T', temp, fluid)

            if phase in ['liquid', 'supercritical_liquid', 'gas', 'supercritical_gas', 'supercritical'] and temp >= temp_melt:
                if fluid == "RP-1":
                    rp1 = RP1Properties()
                    cp = rp1.specific_heat(temp)
                    enth = rp1.enthalpy(temp, pressure_pa)
                    beta = rp1.thermal_expansion_coeff(temp, pressure_pa)
                    viscosity = rp1.viscosity(temp, pressure_pa)
                    density = rp1.density(temp, pressure_pa)
                    conductivity = rp1.thermal_conductivity(temp)
                    vapor_pressure = rp1.vapor_pressure(temp)
                    latent_heat = None
                else:
                    cp = CP.PropsSI('C', 'T', temp, 'P', pressure_pa, fluid)
                    enth = CP.PropsSI('H', 'T', temp, 'P', pressure_pa, fluid) * 1e-3
                    beta = CP.PropsSI('ISOBARIC_EXPANSION_COEFFICIENT', 'T', temp, 'P', pressure_pa, fluid)
                    viscosity = CP.PropsSI('V', 'T', temp, 'P', pressure_pa, fluid)
                    density = CP.PropsSI('D', 'T', temp, 'P', pressure_pa, fluid)
                    conductivity = CP.PropsSI('L', 'T', temp, 'P', pressure_pa, fluid)

                    if phase in ['liquid', 'supercritical_liquid']:
                        vapor_pressure = CP.PropsSI('P', 'T', temp, 'Q', 0, fluid) * 1e-5
                        T_sat = temp  # tu supposes que temp est une température de saturation (à vérifier)
                        try:
                            h_liq = CP.PropsSI('H', 'T', T_sat, 'Q', 0, fluid)
                            h_vap = CP.PropsSI('H', 'T', T_sat, 'Q', 1, fluid)
                            latent_heat = (h_vap - h_liq) * 1e-3  # J/kg -> kJ/kg
                        except ValueError:
                            latent_heat = None
                    else:
                        latent_heat = None
                        vapor_pressure = None
                        
                metrics = [
                    ("Phase", phase),
                    ("Density (kg/m³)", f"{format_number(density)}"),
                    ("Specific Heat Capacity Cp (J/kg·K)", f"{format_number(cp)}"),
                    ("Enthalpy (kJ/kg)", f"{format_number(enth)}"),
                    ("Thermal Expansion Coefficient (1/K)", f"{beta:.3f}"),
                    ("Viscosity (Pa·s)", f"{viscosity:.6f}"),
                    ("Thermal Conductivity (W/m·K)", f"{conductivity:.3f}")
                ]

                # Ajout conditionnel
                if vapor_pressure is not None:
                    metrics.append(("Vapor Pressure (bar)", f"{format_number(vapor_pressure)}"))
                if latent_heat is not None:
                    metrics.append(("Latent Heat (kJ/kg)", f"{format_number(latent_heat)}"))
                if temp_melt != 0:
                    metrics.append((f"Melting temperature of {fluid} (K)", f"{format_number(temp_melt)}"))
                if T_inversion is not None:
                    metrics.append((f"JT inversion temperature of {fluid} (K)", f"{format_number(T_inversion)}"))

                # Affichage du titre
                st.markdown(f'### Properties of {fluid} at {format_number(temp)} K and {format_number(pressure)} bar :')

                # Répartition dans 3 colonnes
                cols = st.columns(3)
                for i, (label, value) in enumerate(metrics):
                    with cols[i % 3]:
                        st.metric(label=label, value=value)
            else:
                st.markdown(f'### Properties of {fluid} at {format_number(temp)} K and {format_number(pressure)} bar :')
                st.write(f'**{fluid}** is in the **solid** phase')
                st.write(f'**Minimal temperature to return to liquid phase :** {format_number(temp_melt)} K')
    except Exception as e:
        st.error(f'Error :{e}')    

with col2:
    if temp_melt == 0:
        st.write(f'**{fluid}** cannot solidify at this pressure.')
        st.write(f'**Minimal pressure to go to solid phase :** 25.3 bar')