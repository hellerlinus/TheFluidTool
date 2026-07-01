import streamlit as st
import numpy as np
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import os

# Page setup
st.set_page_config(page_title="Pressure Drop", layout="wide")
st.title("Pressure Drop Calculator")
#st.markdown("\u26a0\ufe0f Assumes steady-state flow and uniform pipe diameter. CoolProp is used for real gas/liquid properties.")
st.info("This tool allows the computation of the pressure drop of a fluid along a pipe with uniform diameter, assuming steady state flow.  CoolProp is used for real gas/liquid properties.")


diagram_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "Pressure_Drop_Diagram.png")
diagram_path = os.path.abspath(diagram_path)
st.image(diagram_path)


# Add ESA logo to the sidebar
#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)
#st.sidebar.image(logo_path)


# Fluid list
fluids = ['H2O','O2','CH4', 'H2',]

# Pipe materials and their roughness

pipe_materials = {
    "Smooth (glass/plastic)": 1e-8,
    "Commercial steel": 0.000045,
    "Stainless steel": 0.000015,
    "New cast iron": 0.00026,
    "Old cast iron": 0.00085,
    "Concrete (rough)": 0.003,
    "Rusty steel": 0.0015
}


# Create two columns
col1, col2 = st.columns(2)

# Column 1: Pipe & Flow Inputs
with col1:
    st.header("Pipe and Flow Conditions")
    L = st.number_input("Pipe length (m):", 0.01, 100.0, 1.0)
    D = st.number_input("Pipe inner diameter (cm):", 0.1, 100.0, 5.0) / 100
    pipe_type = st.selectbox("Select pipe material:", list(pipe_materials.keys()))
    epsilon = pipe_materials[pipe_type]
    mdot = st.number_input("Mass flow rate (kg/s):", 0.001, 10000.0, 1.0)
    include_height = st.checkbox("Include height difference?", value=False)
    if include_height:
        height_diff = st.number_input("Height difference (m) (Include the sign):", min_value=-100.0, max_value=100.0, value=0.0)
    else:
        height_diff = 0.0

# Column 2: Fluid and Conditions
with col2:
    st.header("Fluid and Conditions")
    fluid = st.selectbox("Select fluid:", fluids)
    P_bar = st.number_input("Inlet pressure (bar):", 0.01, 500.0, 1.0)
    T_K = st.number_input("Temperature (K):", 1.0, 1000.0, 300.0)
    use_variable_rho = st.checkbox("Use variable density ρ(P) (for compressible flow)?", value=True)


# Constants and initialization
P_start = P_bar * 1e5
A = np.pi * (D / 2) ** 2
N = 50
dx = L / N
delta_P_total = 0
P = P_start
rel_roughness = epsilon / D 
if rel_roughness > 0.05:
    st.warning(f"⚠️ Relative roughness ε/D = {rel_roughness:.3f} is outside the valid range for Swamee–Jain. Consider using another Tool.")

c = CP.PropsSI("A", "T", T_K, "P", P, fluid) # speed of sound

# Initial properties
density_0 = CP.PropsSI("D", "T", T_K, "P", P_start, fluid)
viscosity = CP.PropsSI("V", "T", T_K, "P", P_start, fluid)

Re_list = []
flow_regimes = []


pressure_profile = [P_start]
velocity_profile = []


# Main integration loop
for _ in range(N):
    if use_variable_rho:
        try:
            rho = CP.PropsSI("D", "T", T_K, "P", P, fluid)
        except:
            rho = density_0
    else:
        rho = density_0  # Incompressible assumption

    u = mdot / (rho * A)
    Re = rho * u * D / viscosity
    Re_list.append(Re)
    velocity_profile.append(u)             # <-- append velocity
    Ma = u / c

    # Inside the main integration loop, after calculating Re:

    if Re < 2300:
        flow_regimes.append("laminar")
        f = 64 / Re
    elif 2300 <= Re <= 4000:
        flow_regimes.append("transition")
        st.info("⚠️ Flow is in the transitional regime (2300 < Re < 4000). Friction factor estimated using turbulent model.")
        f = 0.25 / (np.log10(rel_roughness / 3.7 + 5.74 / Re**0.9))**2  # Swamee–Jain
    else:
        flow_regimes.append("turbulent")
        f = 0.25 / (np.log10(rel_roughness / 3.7 + 5.74 / Re**0.9))**2  # Swamee–Jain


    dP = f * (dx / D) * (rho * u**2 / 2)
    delta_P_total += dP
    P -= dP  
    pressure_profile.append(P)
    
# Add gravitational pressure difference if height is specified  
g = 9.81  # gravitational acceleration (m/s²)
delta_P_gravity =- density_0 * g * height_diff  # in Pa
delta_P_total += delta_P_gravity

delta_P_bar = delta_P_total / 1e5
delta_P_gravity_bar = delta_P_gravity / 1e5 

# Additional important quantities
u_initial = mdot / (density_0 * A)  # in m/s

# Define fluid-specific velocity limits (m/s)
velocity_limits = {
    "H2O": 10,
    "O2": 25,
    "CH4": 20,
    "H2": 35
}

# Get the limit for the selected fluid (default fallback = 25 m/s)
u_limit = velocity_limits.get(fluid, 25)

if u_initial > u_limit:
    st.warning(f"⚠️ High flow velocity: {u_initial:.2f} m/s exceeds the recommended limit for {fluid} ({u_limit} m/s). Check if such velocities are needed and possibly adapt mass flow rate or diameter to more realistic values.")




pressure_pa = P_bar * 1e5
phase = CP.PhaseSI('P', pressure_pa, 'T', T_K, fluid)

if fluid == "RP-1":
    rp1 = RP1Properties()
    phase = rp1.get_phase(T_K, pressure_pa)
else:
    phase = CP.PhaseSI('P', pressure_pa, 'T', T_K, fluid)

# Criteria for compressible vs incompressible



if phase in ["gas", "supercritical_gas", "supercritical"] and use_variable_rho == False:
    if Ma > 0.3:
        #use_variable_rho = True  # mandatory
        st.warning("⚠️ Compressibility effects are significant (Ma ≥ 0.3). Consider using variable density.")
elif phase == "liquid":
    #use_variable_rho = False  # even if Ma > 0.3, likely negligible
    st.info("Incompressible flow assumption is valid (liquid with Ma < 0.3).")
elif phase in ["two-phase", "mixture"] and use_variable_rho == False:
    #use_variable_rho = True  # always
    st.warning("⚠️ Compressibility effects are significant (Ma ≥ 0.3). Consider using variable density.")





st.header("Results")

col1, col2 = st.columns(2)

with col1:
    st.metric("Estimated Pressure Drop (Decrease)", f"{delta_P_bar:.3f} bar")
    if include_height:
        st.metric("Gravitational Pressure Effect", f"{delta_P_gravity_bar:.3f} bar")
    P_2_bar = P_bar - delta_P_bar
    st.metric("Final Pressuere ", f"{P_2_bar:.3f} bar")
    #if P_2_bar < 0:
     #   st.error(f"❌ Pressure drop ({delta_P_bar:.2f} bar) exceeds inlet pressure ({P_start / 1e5:.2f} bar).")
      #  st.warning(" Make sure conditions are realistic and increase inlet pressure.")

    st.metric("Initial Reynolds Number", f"{Re_list[0]:.0f}")
    #st.metric("Final Reynolds Number", f"{Re_list[-1]:.0f}")
    st.metric("Flow Regime", flow_regimes[-1].capitalize())

with col2:
    st.metric("Initial Flow Velocity", f"{u_initial:.2f} m/s")
    st.metric("Fluid Phase", phase.capitalize())
    st.metric("Mach Number", f"{Ma:.3f}")
    st.metric("Friction Factor", f"{f:.4f}")


col1, col2 = st.columns(2)

# Pressure Change along the pipe

if P_2_bar > 0:
    pressure_profile_bar = np.array(pressure_profile) / 1e5  # Pa to bar
    x_vals = np.linspace(0, L, N + 1)
    with col1:
        st.subheader("Pressure Along the Pipe")
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        ax1.plot(x_vals, pressure_profile_bar, color="royalblue", label="Pressure (bar)")
        ax1.set_xlabel("Distance along pipe (m)")
        ax1.set_ylabel("Pressure (bar)")
        ax1.grid(True)
        ax1.legend()
        st.pyplot(fig1)

    with col2:
        st.subheader("Velocity Along the Pipe")
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        ax2.plot(x_vals[:-1], velocity_profile, color="darkorange", label="Velocity (m/s)")
        ax2.set_xlabel("Distance along pipe (m)")
        ax2.set_ylabel("Velocity (m/s)")
        ax2.grid(True)
        ax2.legend()
        st.pyplot(fig2)



    def plot_moody_chart():
        Re_vals = np.logspace(3, 8, 500)
        fig, ax = plt.subplots(figsize=(8, 5))

        for label, epsilon in pipe_materials.items():
            rel_roughness = epsilon / D
            f_vals = []

            for Re in Re_vals:
                if Re < 2300:
                    f = 64 / Re
                else:
                    f = 0.25 / (np.log10(rel_roughness / 3.7 + 5.74 / Re**0.9))**2
                f_vals.append(f)

            ax.plot(Re_vals, f_vals, label=label)

        # Vertical lines for flow regimes
        ax.axvline(x=2300, color='red', linestyle='--', linewidth=1, label='Transition (Re=2300)')
        ax.axvline(x=4000, color='red', linestyle='--', linewidth=1, label='Fully Turbulent (Re=4000)')
            # Labels for flow regimes
        ax.text(6e2, 0.02, 'Laminar', rotation=0, verticalalignment='center', fontsize=10, color='black')
        #ax.text(4e3, 0.02, 'Transitional', rotation=90, verticalalignment='center', fontsize=10, color='black')
        ax.text(2e5, 0.02, 'Turbulent', fontsize=10, color='black')


        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Reynolds Number')
        ax.set_ylabel('Friction Factor f')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        #ax.set_title("Friction Factor Chart Based on Selected Pipe Types (Computed)")
        ax.legend(loc ='lower right')
        return fig


    st.subheader("Friction Factor Chart Based on Selected Pipe Types")
    moody_fig = plot_moody_chart()
    st.pyplot(moody_fig)


    st.subheader("Pressure Drop vs. Pipe Diameter")

    # Diameters from 0.2 cm to 10 cm
    D_vals = np.linspace(0.002, 0.10, 100)  # in meters
    delta_p_vals = []

    for D_test in D_vals:
        A_test = np.pi * (D_test / 2)**2
        try:
            rho_test = CP.PropsSI("D", "T", T_K, "P", P_start, fluid)
            mu_test = CP.PropsSI("V", "T", T_K, "P", P_start, fluid)
        except:
            continue

        u_test = mdot / (rho_test * A_test)
        Re_test = rho_test * u_test * D_test / mu_test

        # Swamee-Jain friction factor
        rel_eps_test = epsilon / D_test
        if Re_test < 2300:
            f_test = 64 / Re_test
        else:
            f_test = 0.25 / (np.log10(rel_eps_test / 3.7 + 5.74 / Re_test**0.9))**2

        dp_friction = f_test * (L / D_test) * (rho_test * u_test**2 / 2)
        dp_gravity = -rho_test * g * height_diff  # sign consistent with above
        dp_total = dp_friction + dp_gravity
        delta_p_vals.append(dp_total / 1e5)  # convert to bar

    # Plotting
    fig_d, ax_d = plt.subplots(figsize=(6, 4))
    ax_d.plot(np.array(D_vals)*100, delta_p_vals, color='crimson')
    ax_d.set_xlabel("Pipe Diameter D (cm)")
    ax_d.set_ylabel("Pressure Drop Δp (bar)")
    ax_d.set_title("Pressure Drop vs. Pipe Diameter")
    ax_d.grid(True)
    st.pyplot(fig_d)
if P_2_bar < 0:
        st.error(f"❌ Pressure drop ({delta_P_bar:.2f} bar) exceeds inlet pressure ({P_start / 1e5:.2f} bar). Compressible Flow assumption might fail in this case.")
        st.warning(" Make sure conditions are realistic and increase inlet pressure.")