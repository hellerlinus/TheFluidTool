import streamlit as st
import os

# ============================================================
# OPTIONAL COOLPROP
# ============================================================
try:
    import CoolProp.CoolProp as CP
    CP_OK = True
except:
    CP_OK = False


# ============================================================
# PAGE
# ============================================================
st.set_page_config(page_title="Fluid Cost", layout="wide")
st.title("Fluid Calculator")


# ============================================================
# FLUIDS
# ============================================================
FLUIDS = {
    "O2": "Oxygen",
    "N2": "Nitrogen",
    "H2": "Hydrogen",
    "CH4": "Methane",
    "He": "Helium",
    "H2O": "Water",
    "RP-1": None
}

LIQUID_DENSITY = {
    "O2": 1141,
    "N2": 808,
    "H2": 70.8,
    "CH4": 422,
    "He": 125,
    "H2O": 1000,
    "RP-1": 800
}

# Normal conditions for Nm³
T_REF = 288.15
P_REF = 1e5


def get_ref_density(fluid):
    if fluid is None or not CP_OK:
        return None
    try:
        return CP.PropsSI(
            "D",
            "T", T_REF,
            "P", P_REF,
            fluid
        )
    except:
        return None


# ============================================================
# SETUP
# ============================================================


logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../images", "FluidCon.png"))
st.image(logo_path)

st.header("Fluid Delivery Status")

c1, c2 = st.columns(2)

with c1:
    fluid_key = st.selectbox(
        "Fluid",
        list(FLUIDS.keys())
    )
    fluid = FLUIDS[fluid_key]

with c2:

    rho_liq = LIQUID_DENSITY.get(fluid_key)
    rho_ref = get_ref_density(fluid)

    phase_options = ["Gas delivery"]

    if rho_liq is not None:
        phase_options.insert(
            0,
            "Liquid delivery"
        )

    phase = st.radio(
        "Delivery phase",
        phase_options
    )


# ============================================================
# VALIDATION
# ============================================================
if phase == "Liquid delivery" and rho_liq is None:
    st.error("No liquid density available.")
    st.stop()

if phase == "Gas delivery" and rho_ref is None:
    st.error("Gas density unavailable.")
    st.stop()


# ============================================================
# INPUTS
# ============================================================
mass = None
V_L = None
V_Nm3 = None
price_mode = None

c1, c2 = st.columns(2)

if phase == "Liquid delivery":

    with c1:
        input_mode = st.radio(
            "Requirement specified by",
            [
                "Liters (L)",
                "Mass (kg)",
                "Nm³ equivalent"
            ]
        )

    with c2:

        # ----------------------------------
        # INPUT: Liters
        # ----------------------------------
        if input_mode == "Liters (L)":

            V_L = st.number_input(
                "Volume [L]",
                value=1000.0,
                min_value=0.0
            )

            mass = rho_liq * (V_L/1000)

            if rho_ref:
                V_Nm3 = mass/rho_ref

            price_mode = "€/L"


        # ----------------------------------
        # INPUT: Mass
        # ----------------------------------
        elif input_mode == "Mass (kg)":

            mass = st.number_input(
                "Mass [kg]",
                value=1.0,
                min_value=0.0
            )

            V_L = mass/rho_liq*1000

            if rho_ref:
                V_Nm3 = mass/rho_ref

            price_mode = "€/kg"


        # ----------------------------------
        # INPUT: Nm³ equivalent
        # ----------------------------------
        else:

            V_Nm3 = st.number_input(
                "Equivalent Gas Volume [Nm³]",
                value=1000.0,
                min_value=0.0
            )

            mass = rho_ref * V_Nm3
            V_L = mass/rho_liq*1000

            price_mode = "€/Nm³"


# ============================================================
# GAS DELIVERY
# ============================================================
else:

    with c1:
        input_mode = st.radio(
            "Requirement specified by",
            [
                "Nm³",
                "Mass (kg)"
            ]
        )

    with c2:

        if input_mode == "Nm³":

            V_Nm3 = st.number_input(
                "Volume [Nm³]",
                value=1000.0,
                min_value=0.0
            )

            mass = rho_ref*V_Nm3

            price_mode = "€/Nm³"


        else:

            mass = st.number_input(
                "Mass [kg]",
                value=1.0,
                min_value=0.0
            )

            V_Nm3 = mass/rho_ref

            price_mode = "€/kg"


# ============================================================
# PRICING
# ============================================================


price_input = st.number_input(
    f"Price ({price_mode})",
    value=1.0,
    min_value=0.0
)


# ============================================================
# PRICE ENGINE
# ============================================================
if price_mode == "€/kg":
    price_kg = price_input

elif price_mode == "€/Nm³":
    price_kg = price_input/rho_ref

elif price_mode == "€/L":
    price_kg = price_input*1000/rho_liq


price_nm3 = (
    price_kg*rho_ref
    if rho_ref else None
)

price_L = (
    price_kg*rho_liq/1000
    if rho_liq else None
)

total_cost = price_kg*mass


# ============================================================
# OUTPUT
# ============================================================
c1,c2 = st.columns(2)

with c1:

    st.subheader("Physical")

    if rho_liq and V_L is not None:
        st.metric(
            "Liquid Volume",
            f"{V_L:.3f} L"
        )

    if rho_ref and V_Nm3 is not None:
        st.metric(
            "Gas Equivalent",
            f"{V_Nm3:.3f} Nm³"
        )

    st.metric(
        "Mass",
        f"{mass:.5f} kg"
    )

    if rho_liq:
        st.text(f"Liquid density: {rho_liq:.3f} kg/m³")
    if rho_ref:
        st.text(f"Reference gas density: {rho_ref:.6f} kg/m³")


with c2:

    st.subheader("Economics")

    st.metric(
        "€/kg",
        f"{price_kg:.6f}"
    )

    if price_nm3:
        st.metric(
            "€/Nm³",
            f"{price_nm3:.6f}"
        )

    if price_L:
        st.metric(
            "€/L",
            f"{price_L:.6f}"
        )

    st.metric(
        "Total Cost",
        f"{total_cost:.2f} €"
    )


# ============================================================
# WARNINGS
# ============================================================
if not CP_OK:
    st.warning(
        "CoolProp unavailable."
    )



# ============================================================
# FORMULAS
# ============================================================
with st.expander("Formulas", expanded=False):

    st.markdown(r"""
## Liquid delivery

From liters:
$$
m=\rho_{liq}\frac{V_L}{1000}
$$

From mass:
$$
V_L=\frac{m}{\rho_{liq}}1000
$$



---

## Gas delivery

$$
m=\rho_{ref}V_{Nm^3}
$$

$$
V_{Nm^3}
=
\frac{m}{\rho_{ref}}
$$

Reference:
$$
T_{ref}=288.15K
$$

$$
P_{ref}=1 bar
$$

---

## Price conversions

From €/Nm³:
$$
C_{kg}
=
\frac{C_{Nm^3}}
{\rho_{ref}}
$$

From €/L:
$$
C_{kg}
=
\frac{1000C_L}
{\rho_{liq}}
$$

---

## Total Cost

$$
Cost=C_{kg}m
$$
""")