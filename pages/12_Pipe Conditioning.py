import streamlit as st
import numpy as np
import os

# ============================================================
# PAGE
# ============================================================
st.set_page_config(page_title="Pipe Conditioning", layout="wide")
st.title("Conditioning")

P_atm = 101325.0

#logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "ESA_logo_2020_Deep.png"))
#st.sidebar.image(logo_path)

# ============================================================
# INPUTS (COMPACT)
# ============================================================


logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "Cond.png"))
st.image(logo_path)

st.header("Inputs")

col1, col2, col3 = st.columns(3)

# ---------- Fluid ----------
with col1:
    
    fluids = {
        "Air": (1.4, 287.0),
        "Nitrogen": (1.4, 296.8),
        "Helium": (1.66, 2077.0),
        "Hydrogen": (1.41, 4124.0),
    }

    fluid = st.selectbox("Fluid", list(fluids.keys()))
    gamma, R = fluids[fluid]

    T = st.number_input("T [K]", value=300.0)
    P_tank_bar = st.number_input("P_tank [bar]", value=10.0)
    P_tank = P_tank_bar * 1e5

# ---------- Tank ----------
with col2:
   


    

    D = st.number_input("Diameter [m]", min_value=0.00008, value=0.01, step=0.0001, format="%.5f")
    f = st.number_input("Friction f", min_value=0.00000, value=0.02, step=0.0001, format="%.5f")


# ---------- Pipes ----------
with col3:
    L1 = st.number_input("L1 [m]", value=1.0)

    L2 = st.number_input("L2 [m]", value=1.0)

    L3 = st.number_input("L3 [m]", value=1.0)

# ---------- Throttles ----------
st.subheader("Throttles")

col1, col2, col3 = st.columns(3)

with col1:
    d1 = st.number_input("Throttle 1 [m]", min_value=0.00008, value=0.01, step=0.0001, format="%.5f")
with col2:
    d2 = st.number_input("Throttle 2 [m]", min_value=0.00008, value=0.01, step=0.0001, format="%.5f")
with col3:
    Cd = st.number_input("Cd", min_value=0.00008, value=0.98 , step=0.0001, format="%.5f")

# ============================================================
# PRECOMPUTE
# ============================================================
A_pipe = np.pi * D**2 / 4
A1 = np.pi * d1**2 / 4
A2 = np.pi * d2**2 / 4

rc = (2/(gamma+1))**(gamma/(gamma-1))

# ============================================================
# PHYSICS
# ============================================================

def rho(P):
    return P / (R*T)

# ---------------- PIPE ----------------
def pipe(P_in, m_dot, L):
    steps = 40
    dx = L / steps
    P = P_in

    for _ in range(steps):
        density = rho(P)
        V = m_dot / (density * A_pipe)

        dP = f * (dx/D) * (density * V**2 / 2)
        P -= dP
        P = max(P, 1000)

    return P, V

# ---------------- ORIFICE ----------------
def mdot_orifice(Pu, Pd, A):

    ratio = Pd / Pu

    if ratio <= rc:
        return Cd * A * Pu * np.sqrt(gamma/(R*T)) * \
               (2/(gamma+1))**((gamma+1)/(2*(gamma-1)))

    ratio = np.clip(ratio, 1e-6, 0.999)

    return Cd * A * Pu * np.sqrt(
        (2*gamma/(R*T*(gamma-1))) *
        (ratio**(2/gamma) - ratio**((gamma+1)/gamma))
    )

# ---------------- THROTTLE SOLVER ----------------
def solve_throttle(Pu, m_dot, A):

    def res(Pd):
        return mdot_orifice(Pu, Pd, A) - m_dot

    Pd_low = 1e3
    Pd_high = Pu

    for _ in range(60):
        Pd_mid = 0.5*(Pd_low + Pd_high)

        if res(Pd_mid) > 0:
            Pd_high = Pd_mid
        else:
            Pd_low = Pd_mid

    Pd = Pd_mid
    choked = (Pd/Pu) <= rc

    return Pd, choked

# ============================================================
# SYSTEM
# ============================================================
def system(P_tank, m_dot):

    # Pipe 1
    P1, V1 = pipe(P_tank, m_dot, L1)

    # Throttle 1
    P1_out, ch1 = solve_throttle(P1, m_dot, A1)

    # Pipe 2
    P2, V2 = pipe(P1_out, m_dot, L2)

    # Throttle 2
    P2_out, ch2 = solve_throttle(P2, m_dot, A2)

    # Pipe 3
    P3, V3 = pipe(P2_out, m_dot, L3)

    return P1, P1_out, P2, P2_out, P3, V1, V2, V3, ch1, ch2

# ============================================================
# SOLVER
# ============================================================
def solve_mdot(P_tank):

    m_low = 1e-6
    m_high = 5.0

    for _ in range(60):

        m_mid = 0.5*(m_low + m_high)

        *_, P_out, _, _, _, _, _, _, _, _ = system(P_tank, m_mid)

        if P_out > P_atm:
            m_low = m_mid
        else:
            m_high = m_mid

    return m_mid

# ============================================================
# RUN
# ============================================================
m_dot = solve_mdot(P_tank)

P1, P1_out, P2, P2_out, P3, V1, V2, V3, ch1, ch2 = system(P_tank, m_dot)

# ============================================================
# OUTPUT
# ============================================================
st.header("Results")

col1, col2 = st.columns(2)

col1.metric("Mass Flow", f"{m_dot:.4f} kg/s")

col2.metric("Choked T1 / T2", f"{ch1} / {ch2}")

st.subheader("Pressure Distribution")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Tank", f"{P_tank/1e5:.2f} bar")
    st.metric("After Pipe 2", f"{P2/1e5:.2f} bar")

with c2:
    st.metric("After Pipe 1", f"{P1/1e5:.2f} bar")
    st.metric("After Throttle 2", f"{P2_out/1e5:.2f} bar")

with c3:
    st.metric("After Throttle 1", f"{P1_out/1e5:.2f} bar")
    st.metric("Outlet", f"{P3/1e5:.2f} bar")

# ============================================================
# DESIGN MODE
# ============================================================
st.header("Design Mode")

def find_choke_pressure():

    P_low = 1e5
    P_high = 200e5

    for _ in range(50):

        P_mid = 0.5*(P_low + P_high)

        m = solve_mdot(P_mid)
        *_, _, _, _, _, _, _, _, _, ch2 = system(P_mid, m)

        if ch2:
            P_high = P_mid
        else:
            P_low = P_mid

    return P_mid

Pcrit = find_choke_pressure()

st.info("Tank Pressure for Sonic at Throttle 2 = ??")
#st.metric("Tank Pressure for Sonic at Throttle 2", f"{Pcrit/1e5:.2f} bar")

# ============================================================
# FORMULAS
# ============================================================
with st.expander("Engineering Formulas", expanded=False):

    st.markdown(r"""

## Concept

$$
P_{\text{out}}(\dot{m}) = P_{\text{atm}}
$$

---

## Density (Ideal Gas)

$$
\rho = \frac{P}{RT}
$$

---

## Velocity

$$
V = \frac{\dot{m}}{\rho A}
$$

---

## Pipe Loss (Darcy)

$$
dP = f \frac{dx}{D} \frac{\rho V^2}{2}
$$

---

## Orifice Flow

### Choked:
$$
\dot{m} =
C_d A P_u
\sqrt{\frac{\gamma}{RT}}
\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}
$$

### Subsonic:
$$
\dot{m} =
C_d A P_u
\sqrt{
\frac{2\gamma}{RT(\gamma-1)}
\left(
r^{2/\gamma} - r^{(\gamma+1)/\gamma}
\right)
}
$$

---

## Critical Pressure Ratio/Condition

$$
\frac{P_d}{P_u} \le 
\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma}{\gamma-1}}
$$



""")  