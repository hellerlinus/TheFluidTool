import streamlit as st
import numpy as np
import CoolProp.CoolProp as CP
import scipy.optimize as opt
import os

# Page config
st.set_page_config(page_title="Flow Variable", layout="wide")
st.title(" Pressure Drop & Flow Variable Calculator")

st.info("This tool allows the computation of different variables dependent on what is known. It assumes steady-state and incompressible flow and uniform pipe diameter. CoolProp is used for real gas/liquid properties.")

# Add ESA logo to the sidebar
#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)
#st.sidebar.image(logo_path)

diagram_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "Tank_Diagram.png")
diagram_path = os.path.abspath(diagram_path)
st.image(diagram_path)


# --- Select what to compute ---
target = st.selectbox("🔍 Select variable to compute:", [
    "Velocity (u) and Mass Flow Rate (ṁ) from Pressure Drop (∆p)",
    "Velocity (u) and Mass Flow Rate (ṁ) from Time (t)",
    "Flow Time (t) from Velocity (u) or Mass Flow Rate (ṁ)",
    "Pressure Drop (∆p) from Velocity (u) or Mass Flow Rate (ṁ)"
])

col1, col2 = st.columns(2)

with col1:
    fluids = ['H2O','O2', 'CH4', 'H2']
    fluid = st.selectbox("Select fluid:", fluids)
    T_K = st.number_input("Fluid Temperature (K):", 1.0, 1000.0, 300.0)
    if target != "Pressure Drop (∆p) from Velocity (u) or Mass Flow Rate (ṁ)":
        P_bar = st.number_input("Initial Fluid Pressure (bar):", 0.01, 500.0, 1.0)
        P = P_bar * 1e5

        try:
            if fluid == "H2O":
                rho = CP.PropsSI("D", "T", T_K, "Q", 0, fluid)
                mu = CP.PropsSI("V", "T", T_K, "Q", 0, fluid)
            else:
                rho = CP.PropsSI("D", "T", T_K, "P", P, fluid)
                mu = CP.PropsSI("V", "T", T_K, "P", P, fluid)
        except Exception as e:
            st.error(f"⚠️ Could not load properties from CoolProp: {e}")
            st.stop()



g = 9.81

pipe_materials = {
    "Smooth (PVC, brass, copper, glass, other drawn tubing)": 0.0000015,
    "Commercial steel or wrought Iron": 0.000045,
    "Stainless steel": 0.000015,
    "New cast iron": 0.00026,
    "Old cast iron": 0.00085,
    #"Concrete (rough)": 0.003,
    #"Rusty steel": 0.0015
}


def get_pipe_geometry():
    D = st.number_input("Pipe diameter D (cm):", 0.1, 100.0, 2.0) / 100
    L = st.number_input("Pipe length L (m):", 0.01, 5000.0, 10.0)
    A = np.pi * (D / 2) ** 2
    eps = pipe_materials[st.selectbox("Pipe Material:", list(pipe_materials.keys()))]
    eps_rel = eps / D
    delta_h = st.number_input("Height difference ∆h (m) (include sign!):", -100.0, 100.0, 0.0)
    return D, L, A, eps_rel, delta_h

def compute_friction_factor(Re, eps_rel):
    """Compute Darcy friction factor based on flow regime and roughness."""
    if Re < 2300:
        return 64 / Re  # Laminar

    elif 4000 < Re < 1e8 and 1e-6 < eps_rel < 1e-2:
        # Swamee–Jain explicit approximation of Colebrook
        return 0.25 / (np.log10(eps_rel / 3.7 + 5.74 / Re**0.9))**2

    elif 2300 <= Re <= 4000:
        st.warning("Flow is in the transitional regime (2300 < Re < 4000). Friction factor may be inaccurate.")
        # Still use Swamee–Jain as a fallback
        return 0.25 / (np.log10(eps_rel / 3.7 + 5.74 / Re**0.9))**2

    else:
        st.warning(
            f"Outside recommended range for Colebrook approximation:\n"
            f"Re = {Re:.1e}, ε/D = {eps_rel:.1e}\n"
            "Using Swamee–Jain anyway, but results may be inaccurate."
        )
        return 0.25 / (np.log10(eps_rel / 3.7 + 5.74 / Re**0.9))**2

if target == "Velocity (u) and Mass Flow Rate (ṁ) from Pressure Drop (∆p)":
    st.warning("Incompressible flow assumed. Estimates velocity using f ≈ 0.02, then refines using Colebrook equation.")
    with col1: 
        delta_p = st.number_input("Total Pressure Drop (Decrease) ∆p (bar):", 0.01, 100.0, 1.0) * 1e5
    with col2:
        D, L, A, eps_rel, delta_h = get_pipe_geometry()
    delta_p_gravity = rho * g * delta_h
    delta_p_friction = delta_p - delta_p_gravity

    f_guess = 0.02
    u_guess = np.sqrt((delta_p_friction * D) / (f_guess * L * 0.5 * rho))
    Re_guess = rho * u_guess * D / mu

    def colebrook(f, Re, eps_rel):
        return 1.0 / np.sqrt(f) + 2.0 * np.log10(eps_rel / 3.7 + 2.51 / (Re * np.sqrt(f)))

    try:
        f_solution = opt.root_scalar(colebrook, args=(Re_guess, eps_rel), method='brentq', bracket=[0.008, 0.1])
        if not f_solution.converged:
            raise ValueError("Colebrook solver failed")
        f = f_solution.root
    except:
        st.error("❌ Colebrook equation failed. Adjust pipe or fluid parameters.")
        st.stop()

    u = np.sqrt((delta_p_friction * D) / (f * L * 0.5 * rho))
    mdot = rho * A * u
    Re_final = rho * u * D / mu

    delta_p_check = f * (L / D) * (rho / 2) * u**2 + rho * g * delta_h
    delta_p_error = delta_p - delta_p_check
    rel_error = delta_p_error / delta_p * 100

    r1, r2, r3 = st.columns(3)
    r1.metric("Velocity u", f"{u:.3f} m/s")
    r2.metric("Mass Flow ṁ", f"{mdot:.3f} kg/s")
    r3.metric("Reynolds Number", f"{Re_final:.0f}")

    st.divider()
    st.subheader("Diagnostic Info")
    st.markdown(f"""
    - Initial velocity guess: **{u_guess:.2f} m/s**  
    - Computed friction factor: **f = {f:.4f}**  
    - Recomputed ∆p: **{delta_p_check / 1e5:.3f} bar**  
    - Relative error: **{rel_error:.2f}%**
    """)

elif target == "Velocity (u) and Mass Flow Rate (ṁ) from transferred Volume over Time (t)":
        with col2:
            D = st.number_input("Pipe diameter D (cm):", 0.1, 100.0, 2.0) / 100
            A = np.pi * (D / 2) ** 2
            #L = st.number_input("Pipe length L (m):", 0.01, 500.0, 10.0)
            t = st.number_input("Flow time t (s):", 0.1, 10000.0, 3600.0)
            V = st.number_input("Transferred Volume (m^3):", 0.0, 1000.0, 20.0)
            mdot = rho * V / t
            u = mdot / (rho * A)
        with col1:
            st.metric("Velocity u", f"{u:.3f} m/s")
        with col2:
            st.metric("Mass Flow ṁ", f"{mdot:.3f} kg/s")

elif target == "Flow Time (t) from Velocity (u) or Mass Flow Rate (ṁ)":
    with col1:
        input_given = st.radio("Select what is given:", ["Mass Flow Rate (ṁ)", "Velocity (u)"])
    with col2:
        #D, L, A, _, _ = get_pipe_geometry()
        D = st.number_input("Pipe diameter D (cm):", 0.1, 100.0, 2.0) / 100
        A = np.pi * (D / 2) ** 2
        #V = A * L
        V = st.number_input("Transferred Volume (m^3):", 0.0, 1000.0, 20.0)
        if input_given == "Mass Flow Rate (ṁ)":
            mdot = st.number_input("Mass Flow ṁ (kg/s):", 0.001, 1000.0, 1.0)
            t = rho * V / mdot
            u = mdot / (rho * A)
            var = u
        else:
            u = st.number_input("Velocity u (m/s):", 0.01, 100.0, 5.0)
            # t = L / u
            t = V/(u * A)
            mdot = rho * A * u 
            var = mdot
    st.metric("Flow Time t", f"{t:.2f} s")
    if input_given == "Mass Flow Rate (ṁ)":
        st.metric("Flow Velocity", f"{u:.2f} m/s")

    else:
        st.metric("Mass Flow Rate (ṁ)", f"{mdot:.2f} kg/s")


elif target == "Pressure Drop (∆p) from Velocity (u) or Mass Flow Rate (ṁ)":
    with col1:
        input_given = st.radio("Select what is given:", ["Mass Flow Rate (ṁ)", "Velocity (u)"])
        pressure_known = st.radio("Which pressure is given?", ["Initial pressure (p₁)", "Final pressure (p₂)"])
        if pressure_known == "Initial pressure (p₁)":
            p1_bar = st.number_input("Initial pressure p₁ (bar):", 0.01, 500.0, 5.0)
            p1 = p1_bar * 1e5
            p = p1
        else:
            p2_bar = st.number_input("Final pressure p₂ (bar):", 0.01, 500.0, 1.0)
            p2 = p2_bar * 1e5
            p=p2

    with col2:   
        with col2:
            try:
                if fluid == "H2O":
                    rho = CP.PropsSI("D", "T", T_K, "Q", 0, fluid)
                    mu = CP.PropsSI("V", "T", T_K, "Q", 0, fluid)
                else:
                    rho = CP.PropsSI("D", "T", T_K, "P", p, fluid)
                    mu = CP.PropsSI("V", "T", T_K, "P",p, fluid)
            except Exception as e:
                st.error(f"⚠️ Could not load properties from CoolProp: {e}")
                st.stop()


        D, L, A, eps_rel, delta_h = get_pipe_geometry()
        V= A *L
        if input_given == "Mass Flow Rate (ṁ)":
            mdot = st.number_input("Mass Flow ṁ (kg/s):", 0.001, 10000.0, 1.0)
            t = rho * V / mdot
            u = mdot / (rho * A) 
        else:
            u = st.number_input("Velocity u (m/s):", 0.01, 100.0, 5.0)
            t = L / u

    Re = rho * u * D / mu 
    f = compute_friction_factor(Re, eps_rel)
    delta_p_friction = f * (L / D) * (rho / 2) * u**2
    delta_p_gravity = -  rho * g * delta_h
    delta_p_total = delta_p_friction + delta_p_gravity

    if pressure_known == "Initial pressure (p₁)":
        p2 = p1 - delta_p_total
        st.metric("Computed Final Pressure p₂", f"{p2 / 1e5:.3f} bar")
    else:
        p1 = p2 + delta_p_total
        st.metric("Computed Initial Pressure p₁", f"{p1 / 1e5:.3f} bar")
   
    st.metric("Total Pressure Drop (Decrease) ∆p", f"{delta_p_total / 1e5:.3f} bar")

    st.text(f"Re = {Re:.0f}, f = {f:.4f}, u = {u:.2f} m/s, A = {A:.4f} m²")

    Ma = u / CP.PropsSI("A", "T", T_K, "P", p, fluid)
    if Ma > 0.3:
        st.warning(f"⚠️ Mach number is {Ma:.2f} → Compressibility may be non-negligible.")
    if p2 < 0:
        st.error(f"❌ Pressure drop ({delta_p_total / 1e5:.2f} bar) exceeds inlet pressure ({p1 / 1e5:.2f} bar).")
        st.warning(" Make sure conditions are realistic and increase inlet pressure.")


