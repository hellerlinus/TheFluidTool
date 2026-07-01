import streamlit as st
import math
import os

try:
    import CoolProp.CoolProp as CP
    CP_OK = True
except:
    CP_OK = False


# ============================================================
# PAGE
# ============================================================
st.set_page_config(page_title="Water Condensation", layout="wide")
st.title("Condensation")


R_v = 461.5


# ============================================================
# SATURATION FUNCTION
# ============================================================
def psat(T):
    if CP_OK:
        try:
            return CP.PropsSI("P", "T", T, "Q", 1, "Water")
        except:
            pass

    Tc = T - 273.15
    return 610.94 * math.exp((17.625 * Tc) / (Tc + 243.04))


# ============================================================
# DEW POINT
# ============================================================
def dew_point(Pv):
    T_low, T_high = 200, 400
    for _ in range(50):
        T_mid = 0.5 * (T_low + T_high)
        if psat(T_mid) > Pv:
            T_high = T_mid
        else:
            T_low = T_mid
    return T_mid


# ============================================================
# SEALED BOX APP
# ============================================================
with st.expander("Sealed Box Condensation Model", expanded=True):

    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "VaporBox.png"))
    st.image(logo_path)    

  

 

    col1, col2, col3 = st.columns(3)
    

    with col1:
        T1 = st.number_input("T₁ [K]", value=293.15, key="box_T1")

    with col2:
        RH1 = st.number_input("RH₁ (0–1)", value=0.6, key="box_RH")

    with col3:
        T2 = st.number_input("T₂ [K]", value=283.15, key="box_T2")

    V = st.number_input("Volume [m³]", value=1.0, key="box_V")

    Psat1 = psat(T1)
    Pv = RH1 * Psat1
    Psat2 = psat(T2)

    condensation = Pv > Psat2
    RH2 = 1.0 if condensation else Pv / Psat2
    T_dew = dew_point(Pv)

    st.subheader("Step 1 — State Change")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Final RH", f"{RH2*100:.1f}%")
    with c2:
        st.metric("Condensation", "YES" if condensation else "NO")

    st.info(f"Dew point: {T_dew:.2f} K")

    if condensation:

        st.subheader("Step 2 — Condensed Mass")

        rho_v1 = Pv / (R_v * T1)
        m_v1 = rho_v1 * V

        rho_v2 = Psat2 / (R_v * T2)
        m_v2 = rho_v2 * V

        m_cond = max(0.0, m_v1 - m_v2)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Initial Vapor", f"{m_v1*1000:.2f} g")
            st.text("How much water vapor is actually in the air initially.")

        with c2:
            st.metric("Max Vapor", f"{m_v2*1000:.2f} g")
            st.text("maximum vapor mass the cooled air can hold at T2")
        with c3:
            st.metric("Condensed", f"{m_cond*1000:.2f} g")
            st.text("Water mass that had to drop out because cold air can’t hold it.")

        st.info("""
        Box model: Condensation amount is surface-independent.
        
        Implicit assumption: sufficient surface exists to collect condensate.
        """)

    # FORMULAS
    with st.expander("Sealed Box Formulas"):

        st.markdown(r"""
### Saturation pressure
$$
P_{sat}(T) = 610.94 \exp\left(\frac{17.625 (T - 273.15)}{T - 273.15 + 243.04}\right)
$$

### Vapor pressure
$$
P_v = RH_1 \cdot P_{sat}(T_1)
$$

### Condensation condition
$$
P_v > P_{sat}(T_2)
$$

### Final relative humidity
If no condensation:
$$
RH_2=\frac{P_v}{P_{sat}(T_2)}
$$

If condensation occurs:
$$
RH_2=1
$$

### Dew point
$$
P_{sat}(T_{dew}) = P_v
$$

### Condensed mass
$$
m_{cond} = \max(0, m_{v,1} - m_{v,2})
$$

Initial vapor mass
$$
m_{v,1}
=
\frac{P_vV}{R_vT_1}
$$

Maximum vapor mass after cooling
$$
m_{v,2}
=
\frac{P_{sat}(T_2)V}{R_vT_2}
$$

With: $$R_{v}$$ ​= 461.5 J/(kg·K)

""")


# ============================================================
# PIPE MODEL
# ============================================================
with st.expander("Pipe Condensation Model", expanded=False):

    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "VaporPipe.png"))
    st.image(logo_path) 



    col1, col2, col3 = st.columns(3)

    with col1:
        T_air = st.number_input("Ambient T [K]", value=293.15, key="pipe_Tair")

    with col2:
        RH = st.number_input("RH (0–1)", value=0.6, key="pipe_RH")

    with col3:
        T_s = st.number_input("Surface T [K]", value=283.15, key="pipe_Ts")

    Psat_air = psat(T_air)
    Pv = RH * Psat_air

    T_dew = dew_point(Pv)
    condensation = T_s < T_dew

    st.subheader("Step 1 — Check")

    st.metric("Condensation", "YES" if condensation else "NO")
    st.info(f"Dew point: {T_dew:.2f} K")

    if condensation:

        st.subheader("Step 2 — Mass Transfer")

        col1, col2 = st.columns(2)

        with col1:
            D = st.number_input("Diameter [m]", value=0.05, key="pipe_D")

        with col2:
            L = st.number_input("Length [m]", value=1.0, key="pipe_L")

        h_options = {
            "Still air (0.005)": 0.005,
            "Natural convection (0.02)": 0.02,
            "Light airflow (0.1)": 0.1,
            "Fan assisted (0.3)": 0.3,
            "Strong ventilation (0.7)": 0.7
        }

        h = h_options[st.selectbox("Environment", list(h_options.keys()), key="pipe_h")]

        A = math.pi * D * L

        rho_v_air = Pv / (R_v * T_air)
        rho_v_s = psat(T_s) / (R_v * T_s)

        drho = max(0.0, rho_v_air - rho_v_s)

        mdot = h * A * drho

        st.metric("Surface Area", f"{A:.4f} m²")
        st.metric("Condensation Rate", f"{mdot:.8f} kg/s")

    # FORMULAS
    with st.expander("Pipe Model Formulas"):

        st.markdown(r"""
### Vapor pressure
$$
P_v = RH \cdot P_{sat}(T_{air})
$$

### Dew point condition
$$
T_{surface} < T_{dew}
$$

### Surface area
$$
A = \pi D L
$$

### Density difference
$$
\Delta \rho_v = \rho_{v,\infty} - \rho_{v,s}
$$


Ambient vapor density
$$
\rho_{v,\infty}
=
\frac{P_v}{R_vT_{air}}
$$

Surface vapor density
$$
\rho_{v,s}
=
\frac{P_{sat}(T_s)}{R_vT_s}
$$

With: $$R_{v}$$ ​= 461.5 J/(kg·K)

### Condensation rate
$$
\dot{m} = h A \Delta \rho_v
$$


With: $$h$$ = environment-dependent coefficient

""")