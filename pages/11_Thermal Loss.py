import streamlit as st 
import math
import os
import CoolProp.CoolProp as CP

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Thermal Loss", layout="wide")
st.title("Thermal Losses in Piping")

# -----------------------------
# Sidebar logo
# -----------------------------
#logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "ESA_logo_2020_Deep.png"))
#st.sidebar.image(logo_path)

# -----------------------------
# Data
# -----------------------------
fluids = {
    "H2O": {"CoolPropName": "Water"},
    "N2": {"CoolPropName": "Nitrogen"},
    "O2": {"CoolPropName": "Oxygen"},
    "He": {"CoolPropName": "Helium"},
    "CH4": {"CoolPropName": "Methane"},
    "H2": {"CoolPropName": "Hydrogen"},
    "RP-1": {"CoolPropName": None},
}

materials = {
    "Stainless Steel 316": 16.3,
    "Stainless Steel 304": 16.2,
    "Steel": 45,
    "Plastic Polyamide": 0.4,
}

emissivities = {
    "Stainless Steel 316": 0.25,
    "Stainless Steel 304": 0.25,
    "Steel": 0.8,
    "Plastic Polyamide": 0.9,
}

insulations = {
    "None": 0,
    "Perlite": 0.044,
    "Polyurethane Foam": 0.025,
}

standoffs = {
    "G-10": 0.30,       # Glass epoxy laminate (standard cryo support), thermal conductivity
    "G-11": 0.35,       # High-temp version of G10 (slightly higher k)
    "PTFE (Teflon)": 0.25,  # Very low conductivity polymer
}

# -----------------------------
# Helper functions
# -----------------------------
def check_liquid_phase(fluid_cp, T, P):
    """Vérifie si le fluide est liquide à T [K] et P [Pa]"""
    if fluid_cp is None:
        return None  # RP-1 : on suppose liquide
    try:
        phase = CP.PhaseSI('P', P, 'T', T, fluid_cp)
        if phase != "liquid":
            return f"❌ Not liquid → Phase is {phase}"
        return "Liquid"
    except:
        return f"⚠️ Phase check failed for {fluid_cp}"

def get_T_sat_1bar(fluid_name):
    """Retourne la température de saturation à 1 bar"""
    T_sat_1bar = {
        "H2": 20.31,
        "He": 4.30,
        "CH4": 111.50,
        "O2": 90.10,
        "N2": 77.20,
        "H2O": 273.15,
    }
    return T_sat_1bar.get(fluid_name, None)

# -----------------------------
# Diagram selector
# -----------------------------

insulation_type = st.radio("Select insulation type", ["vacuum", "insulation"])


if insulation_type == "vacuum":
    diagram_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "Pipe_Diagram_standoff.png"))
else:
    diagram_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "Pipe_Diagram.png"))
st.image(diagram_file)


# -----------------------------
# Input Parameters
# -----------------------------

# Fluid inputs
with st.expander("Fluid & Environment Inputs", expanded=True):
    f_col1, f_col2, f_col3, f_col4 = st.columns([1,1,1.5,1])

    with f_col1:
        fluid_name = st.selectbox("Fluid", list(fluids.keys()))
        fluid_cp = fluids[fluid_name]["CoolPropName"]
        T_amb = st.number_input("Ambient T (K)", value=298.15)

    with f_col2:
        P_bar = st.number_input("Pressure (bar, absolut)", value=1.0)

    with f_col3:
        T_sat = get_T_sat_1bar(fluid_name)
        label = f"T1 (K) - Liquid if T ≤ {T_sat:.2f} K at 1 bar" if T_sat else "T1 (K)"
        T_in = st.number_input(label, value=300.0)

    with f_col4:
        m_dot = st.number_input("Mass flow (kg/s)", value=1.0, min_value=0.0001)



    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    # ---------------- COL 1 ----------------
    with p_col1:
        material_name = st.selectbox("Material", list(materials.keys()))
        k_pipe = materials[material_name]
        epsilon_pipe = emissivities[material_name]
        epsilon_vessel = emissivities[material_name]

        st.write(f"Insulation type: **{insulation_type}**")

        # ALIGNEMENT pour vacuum
        if insulation_type == "vacuum":
    
            standoff_name = st.selectbox("Standoff material", list(standoffs.keys()))
            k_standoff = standoffs[standoff_name]

    # ---------------- COL 2 ----------------
    with p_col2:
        L = st.number_input("Length (m)", value=10.0)

        if insulation_type == "insulation":
            insulation_name = st.selectbox("Insulation material", list(insulations.keys()))
            k_ins = insulations[insulation_name]
        else:
            st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)

            standoff_per_m = st.number_input(
                "Supports per meter",
                min_value=0.1,
                value=5.0,
                step=0.5
            )

    # ---------------- COL 3 ----------------
    with p_col3:
        D_i_mm = st.number_input("Inner diameter (mm)", value=25.0)
        D_i = D_i_mm / 1000

        if insulation_type == "insulation":
            ins_thickness_mm = st.number_input("Insulation thickness (mm)", value=20.0)
            ins_thickness = ins_thickness_mm / 1000
        else:
            st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)

            standoff_length_mm = st.number_input(
                "Standoff length (mm)",
                min_value=0.1,
                value=10.0,
                step=0.5
            )

    # ---------------- COL 4 ----------------
    with p_col4:
        thickness_mm = st.number_input("Pipe thickness (mm)", value=2.0)
        thickness = thickness_mm / 1000

        if insulation_type == "vacuum":
            st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)

            standoff_diameter_mm = st.number_input(
                "Standoff diameter (mm)",
                min_value=0.1,
                value=3.5,
                step=0.1
            )


    P = P_bar * 1e5  # Pa

    # Vérification phase liquide
    if fluid_name == "RP-1":
        phase = "Liquid (assumed)"
        can_calculate = True
    else:
        phase = check_liquid_phase(fluid_cp, T_in, P)
        can_calculate = phase == "Liquid"

    st.write("**Phase :**", phase)
    if not can_calculate:
        st.warning("Calculation blocked: fluid is not in liquid phase.")
    else:

        # Propriétés fluides
        rho = CP.PropsSI('D','T',T_in,'P',P,fluid_cp) if fluid_cp else 800
        mu = CP.PropsSI('V','T',T_in,'P',P,fluid_cp) if fluid_cp else 1e-3
        k_fluid = CP.PropsSI('L','T',T_in,'P',P,fluid_cp) if fluid_cp else 0.1
        cp = CP.PropsSI('C','T',T_in,'P',P,fluid_cp) if fluid_cp else 2000

        # Flow
        A = math.pi * D_i**2 / 4
        v = m_dot / (rho * A)
        Re = rho * v * D_i / mu
        Pr = cp * mu / k_fluid
        Nu = 0.023 * Re**0.8 * Pr**0.4 if Re > 2300 else 3.66
        h_i = Nu * k_fluid / D_i

        # Geometry
        r_i = D_i / 2
        r_o = r_i + thickness

        # Resistances
        R_conv_i = 1 / (h_i * 2 * math.pi * r_i * L)
        R_pipe = math.log(r_o / r_i) / (2 * math.pi * k_pipe * L)

        if insulation_type == "insulation":
            r_ins = r_o + ins_thickness
            R_ins = math.log(r_ins / r_o) / (2 * math.pi * k_ins * L) if k_ins > 0 and ins_thickness > 0 else 0
            h_o = 10
            R_conv_o = 1 / (h_o * 2 * math.pi * r_ins * L)
            R_total = R_conv_i + R_pipe + R_ins + R_conv_o
        else:
            # Radiation
            sigma = 5.67e-8
            epsilon_pipe = emissivities[material_name]
            if insulation_type == "vacuum":
                epsilon_ext = emissivities[material_name]
            h_rad = sigma * (T_in**2 + T_amb**2) * (T_in + T_amb) / ((1 / epsilon_pipe) + (1 / epsilon_ext) - 1)
            A_rad = 2 * math.pi * r_o * L
            R_rad = 1 / (h_rad * A_rad)

            # Geometry from user inputs
            L_s = standoff_length_mm / 1000
            d_s = standoff_diameter_mm / 1000

            A_s = math.pi * (d_s / 2) ** 2
            N = standoff_per_m * L

            R_standoff = L_s / (k_standoff * A_s * N)

            # Parallel
            R_ext = 1 / (1 / R_standoff + 1 / R_rad)
            R_total = R_conv_i + R_pipe + R_ext

        # Heat transfer
        Q = (T_in - T_amb) / R_total
        delta_T = Q / (m_dot * cp)
        T2 = T_in - delta_T

        # -----------------------------
        # Results
        # -----------------------------
        st.header("Results")
        col1, col2, col3, col4 = st.columns([1,1,1,2])
        col1.metric("Heat transfer Q", f"{Q:.2f} W")
        col2.metric("Temperature drop ΔT", f"{delta_T:.3f} K")
        col3.metric("Outlet Temperature T2", f"{T2:.2f} K")
        col4.metric("Density", f"{rho:.1f} kg/m³")

        st.markdown("### Flow details")
        c1, c2, c3, c4 = st.columns([1,1,1,2])
        c1.metric("Velocity", f"{v:.2f} m/s")
        c2.metric("Reynolds", f"{Re:.0f}")
        c3.metric("Nusselt", f"{Nu:.2f}")
        c4.metric("Convective heat transfer coefficient h_i", f"{h_i:.1f} W/m²K")

        st.info("Q > 0 : Heat loss" if Q > 0 else "Q < 0 : Heat gain (cryo case)")


    # ============================================================
    # ENGINEERING FORMULA REFERENCE (BOTTOM PANEL)
# ============================================================

    with st.expander("Reference (Formulas & Verification)", expanded=False):

        st.markdown(r"""

    **Calculation order:**

    $$
    (T,\ P) \;\rightarrow\; (\rho,\ \mu,\ k,\ c_p)
    $$

    $$
    \dot{m} \;\rightarrow\; v,\ Re,\ Pr,\ Nu,\ h_i
    $$

    $$
    h_i \;\rightarrow\; R_{\text{conv,i}}
    $$

    $$
    R_{\text{conv,i}} + R_{\text{cond}} + R_{\text{ext}} \;\rightarrow\; R_{\text{total}}
    $$

    $$
    R_{\text{total}} \;\rightarrow\; Q \;\rightarrow\; \Delta T \;\rightarrow\; T_2
    $$

    ---

    ## 1. Fluid Properties (CoolProp)

    Density:
    $$
    \rho = \rho(T, P)
    $$

    Dynamic viscosity:
    $$
    \mu = \mu(T, P)
    $$

    Thermal conductivity:
    $$
    k = k(T, P)
    $$

    Specific heat:
    $$
    c_p = c_p(T, P)
    $$

    ---

    ## 2. Flow Properties

    Cross-sectional area:
    $$
    A = \frac{\pi D_i^2}{4}
    $$

    Velocity:
    $$
    v = \frac{\dot{m}}{\rho A}
    $$

    Reynolds number:
    $$
    Re = \frac{\rho v D_i}{\mu}
    $$

    Prandtl number:
    $$
    Pr = \frac{c_p \mu}{k}
    $$

    ---

    ## 3. Internal Convection

    Nusselt number:

    Turbulent (Dittus-Boelter):
    $$
    Nu = 0.023\,Re^{0.8} Pr^{0.4}
    $$

    Laminar:
    $$
    Nu = 3.66
    $$

    Convective heat transfer coefficient:
    $$
    h_i = \frac{Nu \, k}{D_i}
    $$

    ---

    ## 4. Thermal Resistances

    ### Internal convection:
    $$
    R_{\text{conv,i}} = \frac{1}{h_i \, 2\pi r_i L}
    $$

    ### Pipe conduction:
    $$
    R_{\text{pipe}} = \frac{\ln(r_o / r_i)}{2\pi k_{\text{pipe}} L}
    $$

    ---

    ## 5. External Heat Transfer

    ### Case A: Insulation

    Insulation conduction:
    $$
    R_{\text{ins}} = \frac{\ln(r_{\text{ins}} / r_o)}{2\pi k_{\text{ins}} L}
    $$

    External convection:
    $$
    R_{\text{conv,o}} = \frac{1}{h_o \, 2\pi r_{\text{ins}} L}
    $$

    ---

    ### Case B: Vacuum + Radiation + Standoffs

    Radiative heat transfer coefficient:
    $$
    h_{\text{rad}} =
    \sigma (T_1^2 + T_{\text{amb}}^2)(T_1 + T_{\text{amb}})
    \left[
    \frac{1}{\frac{1}{\epsilon_1} + \frac{1}{\epsilon_2} - 1}
    \right]
    $$

    Radiation resistance:
    $$
    R_{\text{rad}} = \frac{1}{h_{\text{rad}} A}
    $$

    Standoff conduction:
    $$
    R_{\text{standoff}} =
    \frac{L_s}{k_s \, A_s \, N}
    $$

    with:
    $$
    A_s = \frac{\pi d_s^2}{4}, \quad N = n_{\text{per m}} \cdot L
    $$

    Parallel combination:
    $$
    R_{\text{ext}} =
    \left(
    \frac{1}{R_{\text{rad}}} + \frac{1}{R_{\text{standoff}}}
    \right)^{-1}
    $$

    ---

    ## 6. Total Thermal Resistance

    Insulated case:
    $$
    R_{\text{total}} =
    R_{\text{conv,i}} + R_{\text{pipe}} + R_{\text{ins}} + R_{\text{conv,o}}
    $$

    Vacuum case:
    $$
    R_{\text{total}} =
    R_{\text{conv,i}} + R_{\text{pipe}} + R_{\text{ext}}
    $$

    ---

    ## 7. Heat Transfer

    Heat transfer rate:
    $$
    Q = \frac{T_1 - T_{\text{amb}}}{R_{\text{total}}}
    $$

    ---

    ## 8. Temperature Drop

    $$
    \Delta T = \frac{Q}{\dot{m} \, c_p}
    $$

    Outlet temperature:
    $$
    T_2 = T_1 - \Delta T
    $$

    ---

    ## 9. Interpretation

    - $Q > 0$ → heat loss to environment  
    - $Q < 0$ → heat gain (typical in cryogenic systems)


    """)    



        


