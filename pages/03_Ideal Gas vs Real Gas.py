import CoolProp.CoolProp as CP
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import os

st.set_page_config(page_title="Ideal Gas vs Real Gas", layout="wide")

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

st.write(f"### Ideal Gas vs Real Gas")

#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)

#st.sidebar.image(logo_path)
#st.image('ESA_logo_2020_Deep.png')

fluids_print = st.multiselect("Choose the fluids", ['H2', 'N2', 'O2', 'He', 'CH4'], default=['H2', 'N2', 'O2'])

T = 288.15
p_min = 1e5  # Pression minimale en Pa (1 bar)
p_max = 1e8  # Pression maximale en Pa (1000 bar)

pressures = np.linspace(p_min, p_max, 100)

comp_2 = go.Figure()

for fluid_print in fluids_print:

    densities_real = []
    densities_ideal = []    

    for p in pressures:
        # Modèle réel (équation d'état complète)
        rho_real = CP.PropsSI('D', 'P', p, 'T', T, fluid_print)
        densities_real.append(rho_real)
        
        # Modèle idéal (loi des gaz parfaits)
        # ρ = P/(R·T) où R est la constante spécifique du gaz
        R_specific = CP.PropsSI('GAS_CONSTANT', fluid_print) / CP.PropsSI('MOLAR_MASS', fluid_print)
        rho_ideal = p / (R_specific * T)
        densities_ideal.append(rho_ideal)

    pressures_bar = [p/1e5 for p in pressures]

    comp_2.add_trace(go.Scatter(x=pressures_bar,y=densities_real,mode='lines',name=f'{fluid_print} - Real gas',line=dict(width=2)))
    comp_2.add_trace(go.Scatter(x=pressures_bar,y=densities_ideal,mode='lines',name=f'{fluid_print} - Ideal gas',line=dict(width=2, dash='dash')))

comp_2.update_layout(
    title=dict(text="Comparison of Ideal Gas vs Real Gas at 15°C", x=0.525, xanchor='center'),
    yaxis_title="Density (kg/m³)",
    xaxis_title="Pressure (bar)",
)

st.plotly_chart(comp_2)

T = 288.15
p_min = 1e5  # Pression minimale en Pa (1 bar)
p_max = 1e8  # Pression maximale en Pa (1000 bar)

pressures = np.linspace(p_min, p_max, 100)

comp_1 = go.Figure()
compressibility_ideal = [1] * len(pressures)
comp_1.add_trace(go.Scatter(x=pressures_bar,y=compressibility_ideal,mode='lines',name=f'Ideal gas',line=dict(width=2, dash='dash')))

for fluid_print in fluids_print:

    compressibility_real = []   

    for p in pressures:
        # Modèle réel (équation d'état complète)
        R_specific = CP.PropsSI('GAS_CONSTANT', fluid_print) / CP.PropsSI('MOLAR_MASS', fluid_print)
        rho_real = CP.PropsSI('D', 'P', p, 'T', T, fluid_print)
        factor_real = p / (rho_real * R_specific * T)
        compressibility_real.append(factor_real)

    pressures_bar = [p/1e5 for p in pressures]

    comp_1.add_trace(go.Scatter(x=pressures_bar,y=compressibility_real,mode='lines',name=f'{fluid_print} - Real gas',line=dict(width=2)))


comp_1.update_layout(
    title=dict(text="Compressibility factor at 15°C", x=0.525, xanchor='center'),
    yaxis_title="Compressibility Factor",
    xaxis_title="Pressure (bar)",
)

st.plotly_chart(comp_1)