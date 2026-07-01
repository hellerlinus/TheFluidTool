import streamlit as st
import numpy as np
import os


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Rocket Thrust", layout="wide")
st.title("Rocket Thrust Calculator")

g0 = 9.81
Ru = 8314

#logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "ESA_logo_2020_Deep.png"))
#st.sidebar.image(logo_path)

# -----------------------------
# Propellants
# -----------------------------
propellants = {
    "LOX / LH2": {"OF_opt": 5.5, "Tc_max": 3700, "mw_range": (9, 16), "gamma_base": 1.20, "At": 0.056, "Ae": 2.6, "E": 45},
    "LOX / RP-1": {"OF_opt": 2.6, "Tc_max": 3700, "mw_range": (20, 28), "gamma_base": 1.22, "At": 0.04, "Ae": 0.2, "E": 5},
    "LOX / CH4": {"OF_opt": 3.5, "Tc_max": 3600, "mw_range": (16, 22), "gamma_base": 1.23, "At": 0.04, "Ae": 0.2, "E": 5},
    "MMH / N2O4": {"OF_opt": 2.0, "Tc_max": 3400, "mw_range": (20, 26), "gamma_base": 1.22, "At": 0.015, "Ae": 0.06, "E": 4},
    "UDMH / N2O4": {"OF_opt": 2.2, "Tc_max": 3400, "mw_range": (20, 26), "gamma_base": 1.23, "At": 0.02, "Ae": 0.08, "E": 4},
    "Aerozine-50 / N2O4": {"OF_opt": 2.2, "Tc_max": 3400, "mw_range": (20, 26), "gamma_base": 1.23, "At": 0.025, "Ae": 0.1, "E": 4},
}

# -----------------------------
# Models
# -----------------------------
def Tc_model(of, opt, max_tc):
    return max_tc - 60*(of-opt)**2

def gamma_model(of, opt, base):
    return base + 0.015*np.exp(-((of-opt)**2)/2)

def mw_model(of, opt, mn, mx):
    span = (mx-mn)/2
    return mn + span*(1 + np.tanh((of-opt)/1.5))

def c_star(Tc, gamma, R):
    return np.sqrt(R*Tc)/gamma * ((gamma+1)/2)**((gamma+1)/(2*(gamma-1)))

def area_mach(M, gamma):
    return (1/M)*((2/(gamma+1)*(1+(gamma-1)/2*M**2))**((gamma+1)/(2*(gamma-1))))

def solve_mach(eps, gamma, tol=1e-6, max_iter=100):
    """
    Solve A/A* = eps for supersonic Mach number (M > 1)
    using bisection method.
    """

    def f(M):
        return area_mach(M, gamma) - eps

    M_low = 1.0001   # just above sonic
    M_high = max(10.0, 2 + 0.5 * eps)    # upper bound (safe for most nozzles)

    # Check bounds
    if f(M_low) * f(M_high) > 0:
        return None  # no solution in range

    for _ in range(max_iter):
        M_mid = 0.5 * (M_low + M_high)
        f_mid = f(M_mid)

        if abs(f_mid) < tol:
            return M_mid

        if f(M_low) * f_mid < 0:
            M_high = M_mid
        else:
            M_low = M_mid

    return M_mid

# -----------------------------
# NEW: optimal ε solver (Pe ≈ Pa)
# -----------------------------
def find_optimal_eps(Pc, gamma, Pa):
    for eps in np.linspace(2, 120, 300):
        Me = solve_mach(eps, gamma)
        if Me:
            Pe = Pc * (1 + (gamma-1)/2 * Me**2)**(-gamma/(gamma-1))
            if abs(Pe - Pa)/max(Pa, 1) < 0.05:
                return eps
    return None

# -----------------------------
# Inputs
# -----------------------------

logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "RockThrust.png"))
st.image(logo_path)

st.header("Inputs")

fuel = propellants[st.selectbox("Propellant", list(propellants.keys()))]

OF = st.slider("O/F Ratio", 1.5, 8.0, float(fuel["OF_opt"]))


Tc_auto = Tc_model(OF, fuel["OF_opt"], fuel["Tc_max"])
gamma_auto = gamma_model(OF, fuel["OF_opt"], fuel["gamma_base"])
mw_auto = mw_model(OF, fuel["OF_opt"], fuel["mw_range"][0], fuel["mw_range"][1])
R_auto = Ru / mw_auto


st.subheader("Thermodynamics")

override = st.checkbox("Override Tc / γ / R")

col1, col2, col3 = st.columns(3)

with col1:
    Tc = st.number_input("Tc (K)", value=float(0), step=10.0)
with col2:
    gamma = st.number_input("γ", value=float(gamma_auto), step=0.01)
with col3:
    R = st.number_input("R (J/kg·K)", value=float(R_auto), step=1.0)

if not override:
    Tc, gamma, R = Tc_auto, gamma_auto, R_auto

st.caption(f"Auto → γ={gamma_auto:.3f} | R={R:.0f} J/kg·K")


# -----------------------------
# Engine conditions
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    Pc = st.number_input("Pc (MPa)", value=10.0)
    Pc = Pc * 1e6

with col2:
    Pa = 101325 if st.radio("Environment", ["Sea Level", "Vacuum"]) == "Sea Level" else 0

# efficiency
eta = st.slider("Efficiency η", 0.85, 1.0, 0.95)

# -----------------------------
# Nozzle
# -----------------------------
mode = st.radio("Nozzle", ["Throat + ε", "Throat + Ae"])

col1, col2 = st.columns(2)

with col1:
    At = st.number_input("At (m²)", value=float(fuel["At"]), step=0.001, format="%.4f")

with col2:
    if mode == "Throat + ε":
        eps = st.number_input("ε", value=float(fuel["E"]))
        Ae = At * eps
    else:
        Ae = st.number_input("Ae (m²)", value=float(fuel["Ae"]), step=0.001, format="%.4f")
        eps = Ae / At

# -----------------------------
# ALWAYS SHOW OPTIMAL ε (NEW)
# -----------------------------
eps_opt = find_optimal_eps(Pc, gamma, Pa)



#if eps_opt:
#    st.success(f"Recommended ε (Pe ≈ Pa): {eps_opt:.1f}")
#
#    diff = abs(eps - eps_opt) / eps_opt
#    if diff < 0.15:
#        st.info("Nozzle is well matched to ambient conditions")
#    else:
#        st.warning("Nozzle not optimally expanded for this environment")
#else:
#    st.warning("No optimal ε found in range")

# -----------------------------
# Performance
# -----------------------------
cstar = c_star(Tc, gamma, R)
mdot = Pc * At / cstar

Me = solve_mach(eps, gamma)

st.header("Performance")

if Me:
    Te = Tc / (1 + (gamma-1)/2 * Me**2)
    Pe = Pc * (Te / Tc)**(gamma/(gamma-1))
    ve = Me * np.sqrt(gamma * R * Te) * eta

    thrust = mdot * ve + (Pe - Pa) * Ae
    Isp = thrust / (mdot * g0)


    st.metric("Thrust", f"{thrust/1000:.1f} kN")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Mass Flow", f"{mdot:.2f} kg/s")
        

    with col2:
        st.metric("Isp", f"{Isp:.1f} s")


    st.header("---")


    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Exhaust Velocity", f"{ve:.0f} m/s")
    with col2:
        st.metric("Characteristic Velocity c*", f"{cstar:.0f} m/s")
    with col3:
        Cf = thrust / (Pc * At)
        st.metric("Thrust Coefficient Cf", f"{Cf:.2f}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Exit Temperature", f"{Te:.0f} K")
    with col2:
        st.metric("Exit Mach", f"{Me:.2f}")
    with col3:
        st.metric("Exit Pressure", f"{Pe:,.0f} Pa")

else:
    st.error("No Mach solution found")


# ============================================================
# NOZZLE PERFORMANCE DASHBOARD (EXPANDABLE)
# ============================================================

with st.expander("Performance Dashboard", expanded=True):



    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 8})

    # -----------------------------
    # Unified physics function
    # -----------------------------
    def performance(eps_val):
        mdot_val = Pc * At / cstar
        Me_val = solve_mach(eps_val, gamma)

        if Me_val is None:
            return None

        Te_val = Tc / (1 + (gamma - 1)/2 * Me_val**2)
        Pe_val = Pc * (Te_val / Tc)**(gamma/(gamma-1))
        ve_val = Me_val * np.sqrt(gamma * R * Te_val) * eta

        thrust_val = mdot_val * ve_val + (Pe_val - Pa) * (At * eps_val)
        Isp_val = thrust_val / (mdot_val * g0)

        return Me_val, thrust_val, Isp_val, Pe_val


    # -----------------------------
    # Range
    # -----------------------------
    eps_range = np.linspace(2, 40, 80)

    # ============================================================
    # ROW 1
    # ============================================================

    col1, col2 = st.columns(2)

    # -------- Me vs ε --------
    with col1:
        Me_plot = []

        for eps_val in eps_range:
            res = performance(eps_val)
            Me_plot.append(res[0] if res else np.nan)

        fig = plt.figure()
        plt.plot(eps_range, Me_plot)
        plt.scatter(eps, Me, s=40)
        plt.xlabel("ε")
        plt.ylabel("Me")
        plt.title("Me vs ε")
        plt.grid()
        st.pyplot(fig)


    # -------- Thrust vs ε --------
    with col2:
        F_plot = []

        for eps_val in eps_range:
            res = performance(eps_val)
            F_plot.append(res[1] if res else np.nan)

        fig = plt.figure()
        plt.plot(eps_range, F_plot)
        plt.scatter(eps, thrust, s=40)
        plt.xlabel("ε")
        plt.ylabel("Thrust (N)")
        plt.title("Thrust vs ε")
        plt.grid()
        st.pyplot(fig)


    # ============================================================
    # ROW 2
    # ============================================================

    col3, col4 = st.columns(2)

    # -------- Isp vs ε --------
    with col3:
        Isp_plot = []

        for eps_val in eps_range:
            res = performance(eps_val)
            Isp_plot.append(res[2] if res else np.nan)

        fig = plt.figure()
        plt.plot(eps_range, Isp_plot)
        plt.scatter(eps, Isp, s=40)
        plt.xlabel("ε")
        plt.ylabel("Isp (s)")
        plt.title("Isp vs ε")
        plt.grid()
        st.pyplot(fig)


    # -------- Expansion quality --------
    with col4:
        ratio_plot = []

        for eps_val in eps_range:
            res = performance(eps_val)
            if res:
                Pe_val = res[3]
                ratio_plot.append(Pe_val / max(Pa, 1))
            else:
                ratio_plot.append(np.nan)

        fig = plt.figure()
        plt.plot(eps_range, ratio_plot)
        plt.axhline(1, linestyle="--")
        plt.scatter(eps, Pe / max(Pa, 1), s=40)

        plt.xlabel("ε")
        plt.ylabel("Pe / Pa")
        plt.title("Expansion Quality")
        plt.grid()
        st.pyplot(fig)
        
# ============================================================
# ENGINEERING FORMULA REFERENCE (BOTTOM PANEL)
# ============================================================

with st.expander("Reference (Formulas & Verification)", expanded=False):

    st.markdown(r"""

**Calculation order:**


$$
O/F \;\rightarrow\; (T_c,\ \gamma,\ M)
$$

$$
M \;\rightarrow\; R = \frac{R_u}{M}
$$

$$
(T_c,\ \gamma,\ R) \;\rightarrow\; c^*
$$

$$
c^* \;\rightarrow\; \dot{m} = \frac{P_c A_t}{c^*}
$$

$$
\dot{m} \;\rightarrow\; F = \dot{m} v_e + (P_e - P_a) A_e
$$

$$
F \;\rightarrow\; I_{sp} = \frac{F}{\dot{m} g_0}
$$

---
## 1. Thermodynamic Properties

**Chamber temperature:**
$$
T_c = T_{\max} - 60\,(O/F - O/F_{\text{opt}})^2
$$
Approximates how combustion temperature peaks at the optimal mixture ratio and decreases away from it.


**Heat capacity ratio:**
$$
\gamma = \gamma_{\text{base}} + 0.015\,e^{-\frac{(O/F - O/F_{\text{opt}})^2}{2}}
$$
Models how gas thermodynamic properties vary slightly with mixture ratio.

**Molecular mass of combustion products:**
$$
M = M_{\min} + \frac{M_{\max}-M_{\min}}{2}\left(1 + \tanh\left(\frac{O/F - O/F_{\text{opt}}}{1.5}\right)\right)
$$
Smoothly transitions exhaust gas molecular weight between fuel-rich and oxidizer-rich conditions.

**Specific gas constant:**
$$
R = \frac{R_u}{M}
$$
Converts molecular mass into a specific gas constant governing thermodynamic behavior of the flow.

---

## 2. Characteristic Velocity

$$
c^* =
\frac{\sqrt{R T_c}}{\gamma}
\left(\frac{\gamma+1}{2}\right)^{\frac{\gamma+1}{2(\gamma-1)}}
$$
Represents ideal combustion performance independent of nozzle expansion.

---

## 3. Choked Mass Flow

$$
\dot{m} = \frac{P_c A_t}{c^*}
$$

---

## 4. Nozzle Geometry

Expansion ratio:
$$
\varepsilon = \frac{A_e}{A_t}
$$

---

## 5. Isentropic Area–Mach Relation

$$
\frac{A}{A^*} =
\frac{1}{M}
\left[
\frac{2}{\gamma+1}
\left(1 + \frac{\gamma-1}{2}M^2
\right)
\right]^{\frac{\gamma+1}{2(\gamma-1)}}
$$
Relates nozzle geometry to flow speed, allowing computation of exit Mach number.

---

## 6. Exit Flow Conditions

Exit temperature:
$$
T_e = \frac{T_c}{1 + \frac{\gamma-1}{2}M_e^2}
$$

Exit pressure:
$$
P_e = P_c
\left(1 + \frac{\gamma-1}{2}M_e^2\right)^{-\frac{\gamma}{\gamma-1}}
$$

---

## 7. Exhaust Velocity

$$
v_e = M_e \sqrt{\gamma R T_e}\,\eta
$$

---

## 8. Thrust Equation

$$
F = \dot{m} v_e + (P_e - P_a)A_e
$$

---

## 9. Performance Metrics

Specific impulse:
$$
I_{sp} = \frac{F}{\dot{m} g_0}
$$

Thrust coefficient:
$$
C_f = \frac{F}{P_c A_t}
$$




""") 