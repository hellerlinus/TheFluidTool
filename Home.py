import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Home", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# HEADER
# ============================================================
st.title("Fluidic Calculation Tool")




# ============================================================
# CARD STYLE CSS
# ============================================================
st.markdown("""
<style>
.card {
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #ddd;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}

.card-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 5px;
}

.card-text {
    font-size: 14px;
    color: #555;
}


</style>
""", unsafe_allow_html=True)

st.markdown(
    "<p style='color:red; font-size:24px;'>"
    " Warning: Results are approximate only. This tool is "
    " meant as a pre-calculation to get an understanding "
    "and a ball park estimate only!"
    "</p>",
    unsafe_allow_html=True
)

#st.caption(
 #   "Note that this tool is not completely accurate. It is meant as a pre-calculation to get an understanding and a ball park estimate!"
  #  )

#st.caption("Not a single tool — but a structured modular simulation environment for thermodynamic and test bench systems..")

st.divider()

# ============================================================
# SYSTEM OVERVIEW
# ============================================================
st.subheader("What This Platform Is")

st.write("""
This platform is a engineering environment designed for quick pre-calculations for diffrent thermodynamic and test bench systems. It is structured as a system of individual interacting modules.


""")


st.divider()



# ============================================================
# HOW TO USE
# ============================================================
st.subheader("How to Use This Platform")

st.write("""
1. Select a module  
2. Adjust input parameters  
3. Run simulation automatically (no setup needed)  
4. Analyze results and system behavior  
""")
st.divider()


# ============================================================
# MODULES
# ============================================================
st.subheader("Simulation Modules")

st.write("""
Here you can find a quick explanation of each module as well as the directory to it.

""")

col1, col2 = st.columns(2)

# ------------------ CONDENSATION ------------------
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Basics of Cryogenic Thermodynamics</div>
        <div class="card-text"> 
        Introduces the fundamental thermodynamic and phase-change principles relevant to cryogenic systems. It explains real gas behavior, phase transitions, and key effects for understanding low-temperature fluid systems.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Cryogenic Thermodynamics Model"):
        st.switch_page("pages/01_Basics of Cryogenic Thermodynamics.py")

# ------------------ TANK ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Characteristics Calculator</div>
        <div class="card-text">
        Computes and displays thermophysical properties of selected fluids at given temperature and pressure, including phase identification and key outputs such as density, specific heat, viscosity, enthalpy, and thermal conductivity.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Characteristics Model"):
        st.switch_page("pages/02_Characteristics.py")


st.write("""

""")

col1, col2 = st.columns(2)

# ------------------ FUTURE MODULES ------------------
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Ideal Gas and Real Gas Comparison</div>
        <div class="card-text">
        Compares real-gas and ideal-gas behavior for selected fluids by evaluating density and compressibility factor across a wide pressure range. It visualizes deviations from ideal gas laws to highlight when real-gas effects become significant.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Ideal Gas vs. Real Gas Model"):
        st.switch_page("pages/03_Ideal Gas vs Real Gas.py")

# ------------------ CHILLDOWN ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Phase Diagram </div>
        <div class="card-text">
        Interactive thermodynamic property calculator for cryogenic and engineering fluids. It computes density, phase, and key thermodynamic limits, and visualizes phase diagrams with saturation and melting boundaries.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Phase Diagram Model"):
        st.switch_page("pages/04_Phase Diagram.py")

st.write("""

""")

col1, col2 = st.columns(2)

# ------------------ TANK ------------------
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Onboard Mass Calculator</div>
        <div class="card-text">
        Estimates onboard fluid mass and equivalent Nm³ from pressure, temperature, and volume. It checks phase validity and computes density before converting to standard reference conditions.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Onboard Mass Model"):
        st.switch_page("pages/05_Onboard Mass.py")



# ------------------ CHILLDOWN ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Gas Refill Calculator </div>
        <div class="card-text">
        Estimates the required pressurant gas flow to maintain constant tank pressure during liquid depletion. It models real-gas behavior and thermal effects to size inflow and storage requirements.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Gas Refill Model"):
        st.switch_page("pages/06_Gas Refilling.py")









st.write("""

""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Pressure drop Calculator </div>
        <div class="card-text">
        Computes pressure losses in pipes using Darcy–Weisbach integration with fluid properties. It models friction, gravity effects, and compressibility while tracking pressure, velocity, and flow regime along the pipe.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Pressure drop Model"):
        st.switch_page("pages/07_Pressure Drop.py")

# ------------------ TANK ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Flow Variable Calculator</div>
        <div class="card-text">
        Solves pressure drop, velocity, flow rate, or flow time in pipes using incompressible flow assumptions. It combines fluid properties with friction factor correlations to consistently link hydraulic and thermodynamic variables.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Flow Variable  Model"):
        st.switch_page("pages/08_Flow Variable.py")

st.write("""

""")

col1, col2 = st.columns(2)

# ------------------ CHILLDOWN ------------------
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Water Condensation Calculator </div>
        <div class="card-text">
        Models water vapor condensation in enclosed volumes and on cold surfaces using dew point and saturation pressure relationships. It estimates when condensation occurs and quantifies condensate mass or deposition rate based.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Water Condensation Model"):
        st.switch_page("pages/09_Water Condensation.py")

# ------------------ CHILLDOWN ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Fluid cost Calculator </div>
        <div class="card-text">
        Converts between liquid and gas quantities using real and reference densities to support consistent sizing across phases. It also standardizes pricing between €/kg, €/L, and €/Nm³ to estimate total fluid cost for delivery or storage.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Fluid cost Model"):
        st.switch_page("pages/10_Fluid Cost.py")

st.write("""

""")

col1, col2 = st.columns(2)

# ------------------ TANK ------------------
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Thermal Losses Calculator</div>
        <div class="card-text">
        Estimates heat transfer along cryogenic and thermal piping systems using combined convection, conduction, and radiation models. It calculates heat loss, temperature drop, and outlet conditions based on flow regime, insulation, and structural supports.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Thermal Losses Model"):
        st.switch_page("pages/11_Thermal Loss.py")

# ------------------ TANK ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Pipe Conditioning Calculator</div>
        <div class="card-text">
        Models gas conditioning and pressure losses through pipes and throttles using compressible flow and choked orifice equations. It estimates mass flow rate and pressure evolution in multi-stage flow networks under steady-state assumptions.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Pipe Conditioning Model"):
        st.switch_page("pages/12_Pipe Conditioning.py")

st.write("""

""")

col1, col2 = st.columns(2)

# ------------------ TANK ------------------
with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">Rocket Thrust Calculator</div>
        <div class="card-text">
        Estimates rocket engine performance using simplified thermodynamic and isentropic nozzle flow models. It computes thrust, specific impulse, and key flow conditions based on propellant choice, mixture ratio, and nozzle geometry.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Rocket Thrust Model"):
        st.switch_page("pages/13_Rocket Thrust.py")


# ------------------ CHILLDOWN ------------------
with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">Future Calculators </div>
        <div class="card-text">
        more pages to come...
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.caption("Designed for engineering insight, not high-fidelity CFD simulation.")
