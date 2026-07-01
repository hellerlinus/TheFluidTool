import streamlit as st
import numpy as np
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import os
import pandas as pd

# Page setup
st.set_page_config(page_title="Cryogenic Thermodynamics Essentials", layout="wide")
st.title("Cryogenic Thermodynamics Essentials")
#st.markdown("\u26a0\ufe0f Assumes steady-state flow and uniform pipe diameter. CoolProp is used for real gas/liquid properties.")
st.info("Learn about the basics of thermodynamics needed to understand this tool.")


# Add ESA logo to the sidebar
#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)
#st.sidebar.image(logo_path)


st.markdown("### Fluid Phases & Phase Changes")


st.markdown("""
- **Phases of Matter**: Substances exist as solid, liquid, or gas depending on pressure and temperature.

- **Phase Change ≠ Temperature Change**: During melting, boiling, or condensation, **temperature remains constant** while energy is added or removed (latent heat).
""")
im_phase_change = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "im_phase_change.png")
im_phase_change_path = os.path.abspath(im_phase_change)
st.image(im_phase_change_path, width = 600)



st.markdown("""
- **Boiling Point**: The temperature at which liquid turns to vapor. It increases with pressure.  
Example: Hydrogen boils at 20.3 K under 1 bar, but later at ~23 K under 2 bar.

- **Triple Point**: The unique combination of pressure and temperature where solid, liquid, and vapor phases coexist in equilibrium.

- **Critical Point**: The end of the liquid-vapor boundary. Beyond this, the substance becomes a **supercritical fluid** — no distinct liquid or gas phase exists.  
At this point, increasing pressure **cannot** liquefy the gas.

- **Latent Heats**:  
- **Melting (fusion)**: Energy required to transition from solid to liquid.  
- **Vaporization**: Energy to go from liquid to gas.  
- These are **reversible**: the same energy is released during freezing or condensation.
""")

im_phase_diagram = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "im_phase_diagram.png")
im_phase_diagram_path = os.path.abspath(im_phase_diagram)
st.image(im_phase_diagram_path, width = 350 )

st.markdown("### Gas Phases and Behavior")
st.markdown("""
- **Ideal Gas**: Obeys $pV = nRT$; valid at high temperature and low pressure ($T \gg T_\mathrm{boil}$).
- **Real Gas**: Deviates from ideal behavior due to intermolecular forces; important at low $T$ and high $p$.
- **Vapor**: Gas near its condensation point, not behaving ideally. it is harder to compress than a real gas.
- **Vapor Pressure**: Pressure of a vapor in thermodynamic equilibrium with its liquid at a given temperature.
- **Saturated Vapor**: In equilibrium with its liquid; pressure depends only on temperature. 
            Compression doesn't reduce volume much, but instead causes condensation.
- **Superheated Vapor**: Temperature exceeds boiling point at given pressure; behaves more like a gas.
""")


st.markdown("### Joule-Thomson Effect")

st.markdown("""
- **Intuitive Idea**:  
  When a gas expands through a throttle (like a valve or porous plug) without heat exchange, it can **cool** or **warm** depending on its temperature and molecular structure.
  That's because the expansion reduces the pressure. If molecules attract each other, energy is used to separate them — resulting in cooling. 
    If repulsive forces dominate, the gas heats instead.

- **Joule-Thomson Coefficient ($\mu_{JT}$)**:  
  $$ \mu_{JT} = \left(\\frac{\\partial T}{\\partial p}\\right)_H $$
  - **$\mu_{JT} > 0$** → gas cools during expansion  
  - **$\mu_{JT} < 0$** → gas warms during expansion

- **Inversion Temperature**:  
  The temperature **below** which a gas **cools** when expanded. **Above** it, the gas **heats**.  At this temperature, the Joule-Thompson coefficient is therefore zero.
  This is crucial in cryogenics — gases like hydrogen and helium must be **pre-cooled**.
""")

# Inversion temperature table
jt_data = {
    "Gas": ["Helium", "Hydrogen", "Nitrogen", "Oxygen", "Methane"],
    "Approx. Inversion Temperature [K]": [40, 202, 607, 764, 530]
}
df_jt = pd.DataFrame(jt_data)
st.table(df_jt)


st.markdown("### Heat Capacity")
st.markdown("""
**Heat Capacity** is the amount of energy required to raise a substance’s temperature; hydrogen has an exceptionally high value, making it ideal for pre-cooling systems.
- Hydrogen has **very high heat capacity**: ~14× higher than air.
- Useful for **pre-cooling** systems without large temperature increase.
""")

st.markdown("### Liquefaction Temperatures of Cryogenic Fluids")

st.markdown("""
The **boiling point** marks the temperature at which cryogenic fluids begin to vaporize.  
In cryogenic applications, fluids are often stored near this point — so even small heat inputs can trigger **rapid boiling**.

During this phase change, cryogenic liquids expand **drastically** in volume — turning 1 liter of liquid into **hundreds of liters of gas**.  
Without proper venting, this can lead to dangerous **pressure spikes** or even **explosions** in closed systems.
""")

# Boiling point table
liq_data = {
    "Substance": ["Methane", "Oxygen", "Argon", "Nitrogen", "Neon", "Hydrogen", "Helium"],
    "Boiling Point (K @ 1 bar)": [111.6, 90.2, 87.3, 77.3, 27.1, 20.3, 4.2]
}
df_liq = pd.DataFrame(liq_data)
st.table(df_liq)

st.markdown("### Safety and Reactivity")

im_flammability = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "im_flammability.png")
im_flammability_path = os.path.abspath(im_flammability)
st.image(im_flammability_path, width = 700)

st.markdown("""
- **Hydrogen**: Flammable from 4–75% in air; ignites with very low energy (~0.013 mJ at 22% concentration).
            Invisible flame.
- **Oxygen**: Powerful oxidizer; may ignite contaminants under high flow (Waterhammer risk).
- **Methane**: Flammable; dangerous in BLEVE scenarios when rapid expansion occurs.
- **Nitrogen**: Non-flammable, but can displace oxygen and cause asphyxiation.
""")

