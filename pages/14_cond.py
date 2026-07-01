import streamlit as st
import numpy as np

# =====================================================
# PAGE
# =====================================================
st.set_page_config(page_title="Gas Flow Estimator", layout="centered")

st.title("Gas Flow Estimator")

st.info(
    "This tool provides a first-order engineering estimate of gas flow "
    "through a pipe with two throttles."
)

P_ATM = 101325.0

# =====================================================
# INPUTS
# =====================================================

fluids = {
    "Air": (1.40, 287.0),
    "Nitrogen": (1.40, 296.8),
    "Helium": (1.66, 2077.0),
    "Hydrogen": (1.41, 4124.0),
}

st.header("Inputs")

fluid = st.selectbox("Fluid", fluids.keys())
gamma, R = fluids[fluid]

T = st.number_input("Temperature [K]", value=300.0)

P_tank_bar = st.number_input("Tank Pressure [bar]", value=10.0)
P_tank = P_tank_bar * 1e5

D = st.number_input("Pipe Diameter [m]", value=0.020)
L = st.number_input("Pipe Length [m]", value=3.0)

d1 = st.number_input("Throttle 1 Diameter [m]", value=0.010)
d2 = st.number_input("Throttle 2 Diameter [m]", value=0.008)

Cd = st.number_input("Discharge Coefficient", value=0.98)

f = st.number_input("Pipe Friction Factor", value=0.02)

# =====================================================
# GEOMETRY
# =====================================================

A_pipe = np.pi * D**2 / 4
A1 = np.pi * d1**2 / 4
A2 = np.pi * d2**2 / 4

critical_ratio = (2 / (gamma + 1)) ** (gamma / (gamma - 1))

# =====================================================
# CHOKED MASS FLOW
# =====================================================

def choked_massflow(Pu, A):
    return (
        Cd
        * A
        * Pu
        * np.sqrt(gamma / (R * T))
        * (2 / (gamma + 1))
        ** ((gamma + 1) / (2 * (gamma - 1)))
    )

# =====================================================
# FLOW ESTIMATE
# =====================================================

m1 = choked_massflow(P_tank, A1)
m2 = choked_massflow(P_tank, A2)

m_dot = min(m1, m2)

if m1 < m2:
    limiting = "Throttle 1"
else:
    limiting = "Throttle 2"

# =====================================================
# PIPE ESTIMATE
# =====================================================

rho = P_tank / (R * T)

velocity = m_dot / (rho * A_pipe)

dP_pipe = f * (L / D) * rho * velocity**2 / 2

P_out = max(P_tank - dP_pipe, P_ATM)

# =====================================================
# RESULTS
# =====================================================

st.header("Estimated Results")

col1, col2 = st.columns(2)

col1.metric("Estimated Mass Flow", f"{m_dot:.3f} kg/s")
col2.metric("Estimated Pipe Velocity", f"{velocity:.1f} m/s")

st.metric("Estimated Pipe Pressure Loss", f"{dP_pipe/1e5:.2f} bar")

st.metric("Estimated Outlet Pressure", f"{P_out/1e5:.2f} bar")

st.metric("Limiting Component", limiting)

st.subheader("Throttle Status")

status1 = "Choked (Limiting)" if limiting == "Throttle 1" else "Not Limiting"
status2 = "Choked (Limiting)" if limiting == "Throttle 2" else "Not Limiting"

c1, c2 = st.columns(2)

c1.metric("Throttle 1", status1)
c2.metric("Throttle 2", status2)

# =====================================================
# NOTES
# =====================================================

with st.expander("Model Assumptions"):

    st.markdown("""
This estimator assumes:

- Ideal gas
- Constant temperature
- Steady-state flow
- Constant friction factor
- Standard compressible orifice equations
- Pipe pressure loss estimated using Darcy-Weisbach
- Minor losses are neglected

The results should be used for **preliminary engineering estimates only** and
not as a replacement for detailed compressible flow calculations.
""")