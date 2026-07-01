import CoolProp.CoolProp as CP
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from math import ceil, floor
from typing import Tuple
import pandas as pd
import os

st.set_page_config(page_title="Phase Diagram", layout="wide")

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
    
def helium_melting_pressure(temperature):
    T_min = 1
    if temperature > T_min:
        P = 25.3 + 1.72 * (temperature - 1.0)**2.89  # Pression en bar
    else:
        P = 25.3
    return P

def helium_melting_temperature(pressure_bar):
    p_min = 25.3
    if pressure_bar < p_min:
        T = 0
    else:
        T = 1.0 + ((pressure_bar - 25.3) / 1.72) ** (1 / 2.89)
    return T

def lambda_transition_temperature(P):
    return 2.17 + 0.012 * P - 0.0003 * P ** 2

def get_melting_temperature(fluid, pressure_bar, p_triple, t_triple):
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
    
def find_pressure(T_target, TT_melt, PP_melt):
    idx = min(range(len(TT_melt)), key=lambda i: abs(TT_melt[i] - T_target))
    return PP_melt[idx]

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
    
def melting_temperature_CH4(P):
    pressure_GPa = P / 1e4  
    P_offset = 1.17e-5  # Correction de pression
    A = 0.208           # Coefficient
    T_ref = 90.6941     # Température de référence (K)
    exponent = 1.698    # Exposant
    T = T_ref * (( (pressure_GPa - P_offset) / A ) + 1) ** (1 / exponent)
    return T

fluids = ['H2O', 'N2', 'O2', 'He', 'CH4', 'H2', 'RP-1'] # GN2 / GOX / LH2 / LOX / GHE / LHE / LCH4 / GCH4

#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)

#st.sidebar.image(logo_path)
#st.image('ESA_logo_2020_Deep.png')

st.write(f"### Phase diagram")

col1, col2 = st.columns([1, 1.75])

with col1:
    st.write('')
    st.write('')
    fluid = st.selectbox('Select fluid : ', fluids)
    if fluid != 'RP-1':
        state = CP.AbstractState('HEOS', fluid)
        pc = state.keyed_output(CP.iP_critical)
        pmax = state.keyed_output(CP.iP_max)
        p_triple = state.keyed_output(CP.iP_triple)
        t_min_phase, t_max_phase = get_phase_temp_limits(fluid)
        R = CP.PropsSI("GAS_CONSTANT", fluid) / CP.PropsSI("M", fluid)
        pressure = st.number_input("Enter pressure (bar) : ", min_value = 0.001, max_value = 1000.0, value = 1.0, step = 0.1)
        temp_melt = get_melting_temperature(fluid, pressure, p_triple * 1e-5, t_min_phase)
        pressure_pa = pressure * 1e5
        temp = st.number_input("Enter temperature (K) : ", min_value = 0.0, max_value = 1000.0, value = (t_min_phase + t_max_phase) /2)
        T_inversion = calculer_temperature_inversion_JT(fluid, pressure_pa, t_max_phase)
        data = {
            '': ["Triple point", "Critical point"],
            "Temperature (K)": [ceil_decimals(t_min_phase, 2), ceil_decimals(t_max_phase, 2)],
            "Pressure (bar)": [ceil_decimals(p_triple * 1e-5, 3), ceil_decimals(pc * 1e-5, 2)]
        }
        if fluid == "RP-1":
            rp1 = RP1Properties()
            phase = rp1.get_phase(temp, pressure_pa)
        else:            
            phase = CP.PhaseSI('P', pressure_pa, 'T', temp, fluid)
        st.write('**Phase :**', phase)
        df = pd.DataFrame(data).set_index("")
        st.dataframe(df) 
    else:
        rp1 = RP1Properties()
        t_min_phase = rp1.T_triple
        t_max_phase = rp1.Tc
        p_triple = rp1.P_triple
        pc = rp1.Pc
        pmax = 5000 * 1e10
        pressure = st.number_input("Enter pressure (bar) : ", min_value=0.001, max_value=1000.0, value=1.0, step=0.1)
        temp_melt = rp1.get_melting_temperature(pressure)
        pressure_pa = pressure * 1e5
        temp = st.number_input("Enter temperature (K) : ", min_value=0.0, max_value=1000.0, value=((t_min_phase + t_max_phase) / 2))
        T_inversion = rp1.get_JT_inversion_temp()
        
        # Properties dataframe
        st.write()
        data = {
            '': ["Triple point", "Critical point"],
            "Temperature (K)": [ceil_decimals(t_min_phase, 2), ceil_decimals(t_max_phase, 2)],
            "Pressure (bar)": [ceil_decimals(p_triple * 1e-5, 6), ceil_decimals(pc * 1e-5, 2)]
        }
        df = pd.DataFrame(data).set_index("")
        st.dataframe(df)


with col2:
    graph = go.Figure()

    PP_melt = np.logspace(np.log10(p_triple * 1e-5), np.log10(pmax * 1e-5), 1000)

    if fluid == "H2":
        TT_melt = [melting_temperature_H2(p) for p in PP_melt]
    elif fluid == 'N2':
        TT_melt = [nitrogen_melting_temperature(p) for p in PP_melt]
    elif fluid == 'He':
        TT_melt = np.linspace(0, 50 * t_max_phase, 1000)
        PP_melt = np.where(TT_melt < 1, 25.3, [helium_melting_pressure(T) for T in TT_melt])
        P_lambda = np.linspace(0.05, 30, 1000)
        T_lambda = lambda_transition_temperature(P_lambda)
    elif fluid =='CH4':
        TT_melt = [melting_temperature_CH4(p) for p in PP_melt]
    elif fluid =='RP-1':
        TT_melt = [rp1.get_melting_temperature(p * 1e-5) for p in PP_melt]
    else:
        if fluid == 'H2O':
            PP_melt = np.logspace(np.log10(ceil_decimals(p_triple, 0)), np.log10(pmax), 1000)
        else:
            PP_melt = np.logspace(np.log10(p_triple), np.log10(pmax), 1000)
        TT_melt = [state.melting_line(CP.iT, CP.iP, p) for p in PP_melt]
    
    if fluid in ['H2O', 'O2', 'RP-1']:
        graph.add_trace(go.Scatter(x=TT_melt, y=PP_melt * 1e-5, mode='lines', name='Melting Curve', line=dict(color='blue')))
    else:
        graph.add_trace(go.Scatter(x=TT_melt, y=PP_melt, mode='lines', name='Melting Curve', line=dict(color='blue')))

    TT_sat = np.linspace(t_min_phase, t_max_phase, 1000)
    if fluid != 'RP-1':
        PP_sat = CP.PropsSI('P', 'T', TT_sat, 'Q', 0, fluid)
        graph.add_trace(go.Scatter(x=TT_sat, y=PP_sat * 1e-5, mode='lines', name='Saturation Curve', line =dict(color='orange')))
    else:
        PP_sat = [rp1.vapor_pressure(T) for T in TT_sat]
        graph.add_trace(go.Scatter(x=TT_sat, y=PP_sat, mode='lines', name='Saturation Curve', line=dict(color='orange')))


    x_value_gas = 1.125 * ((t_min_phase + t_max_phase) / 2) 
    y_value_gas = 0.5 * np.sqrt(p_triple * pc) * 1e-5 
    x_value_solid = 0.5 * t_min_phase 
    y_value_solid = 1.125 * np.sqrt(p_triple * pc) * 1e-5 

    if fluid == 'O2':
        x_value_liquid = 0.8 * ((t_min_phase + t_max_phase) / 2) 
        y_value_liquid = 0.2 * pc * 1e-5 
    elif fluid == 'He':
        x_value_liquid = 1 * ((t_min_phase + t_max_phase) / 2) 
        y_value_liquid = 3 * pc * 1e-5 
        x_value_solid = t_min_phase 
        y_value_solid = 3 * helium_melting_pressure(t_min_phase)
    else:
        x_value_liquid = 0.875 * ((t_min_phase + t_max_phase) / 2) 
        y_value_liquid = 0.425 * pc * 1e-5     

    graph.add_annotation(
        x=x_value_gas,
        y=np.log10(y_value_gas),  # Position Y du texte
        text="Gas",  # Le texte à afficher
        showarrow=False,
        font=dict(size=20, color="black"),  # Style de la police
        align="center"  # Alignement du texte
    )

    graph.add_annotation(
        x=x_value_liquid,
        y=np.log10(y_value_liquid),  # Position Y du texte
        text="Liquid",  # Le texte à afficher
        showarrow=False,
        font=dict(size=20, color="black"),  # Style de la police
        align="center"  # Alignement du texte
    )

    graph.add_annotation(
        x=x_value_solid,
        y=np.log10(y_value_solid),  # Position Y du texte
        text="Solid",  # Le texte à afficher
        showarrow=False,
        font=dict(size=20, color="black"),  # Style de la police
        align="center"  # Alignement du texte
    )

    if fluid == 'He':
        graph.add_trace(go.Scatter(x=T_lambda, y=P_lambda, mode='lines', name='Transition Lambda', line=dict(color='grey')))

    graph.add_trace(go.Scatter(x=[t_max_phase, t_max_phase], 
                            y=[1e-3, 1e10], 
                            mode='lines', 
                            line=dict(dash='dash', color='red'), 
                            name='Critical Temp'))
    if fluid !='He':
        graph.add_trace(go.Scatter(x=[temp_melt, t_max_phase],
                                y=[pc * 1e-5, pc * 1e-5], 
                                mode='lines', 
                                line=dict(dash='dash', color='black'), 
                                name='Critical Pressure'))

    if fluid == 'He':
        graph.add_trace(go.Scatter(x=[t_min_phase], y=[p_triple * 1e-5], mode='markers', name ='Lambda Point', marker=dict(size=10, color='green')))
    else :
        graph.add_trace(go.Scatter(x=[t_min_phase], y=[p_triple * 1e-5], mode='markers', name ='Triple Point', marker=dict(size=10, color='green')))

    graph.add_trace(go.Scatter(x=[t_max_phase], y=[pc * 1e-5], mode='markers', name ='Critical Point', marker=dict(size=10, color='purple')))

    graph.add_trace(go.Scatter(x=[temp], y=[pressure], mode='markers', name ='Selected Point', marker=dict(size=10, color='red')))

    graph.update_layout(
        title=dict(text=f'Phase diagram of {fluid}', x=0.425, xanchor='center'),
        xaxis_title='Temperature (K)',
        yaxis_title='Pressure (bar)',
        yaxis_type='log',
        showlegend=True,
        xaxis=dict(showgrid=True, gridcolor='rgba(128, 128, 128, 0.3)', range=[0.4 * temp, 1.75 * temp]),
        yaxis=dict(showgrid=True, gridcolor='rgba(128, 128, 128, 0.3)', range=[np.log10((0.05  * pressure_pa) * 1e-5), np.log10((1000 * pressure_pa) * 1e-5)], tickvals=[1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9], ticktext=['10¯³', '10¯²', '10¯¹', '1', '10¹','10²', '10³', '10⁴', '10⁵', '10⁶', '10⁷', '10⁸', '10⁹']),
    )

    st.plotly_chart(graph)