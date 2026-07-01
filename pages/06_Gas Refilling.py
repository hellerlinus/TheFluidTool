import streamlit as st
import numpy as np
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import os
from scipy.optimize import fsolve
from math import ceil

# Page setup
st.set_page_config(page_title="Gas Refilling", layout="wide")
st.title("Gas-refill in Run Tank for constant Pressure")
#st.markdown("\u26a0\ufe0f Assumes steady-state flow and uniform pipe diameter. CoolProp is used for real gas/liquid properties.")
st.info("This tool can be used to estimate the required gas inflow to compensate the outflow of a liquid in order to maintain constant pressure, assuming uniform in- and outflow.  CoolProp is used for real gas/liquid properties. ")
# Add ESA logo to the sidebar
#logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "ESA_logo_2020_Deep.png")
#logo_path = os.path.abspath(logo_path)
#st.sidebar.image(logo_path)

diagram_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../images", "Nitrogen_Tank_Diagram.png")
diagram_path = os.path.abspath(diagram_path)
st.image(diagram_path)



# Fluid list
fluids = ['H2', 'O2', 'CH4', 'H2O']
gases = ['N2', 'He']


# Get liquid density at tank pressure and liquid temperature


# Column 1: Pipe & Flow Inputs
col1, col2 = st.columns(2)

with col1:
    liquid = st.selectbox("Select the liquid in the tank:", fluids)
    gas = st.selectbox("Select the pressure gas in the tank:", gases)
    
    P_bar = st.number_input("Target pressure in the tank (bar):", 0.01, 500.0, 2.0)
    
    T_K_l = st.number_input("Temperature of the liquid (K):", 1.0, 1000.0, 20.0)
    #T_K_g = st.number_input("Temperature of the gas (K):", 1.0, 1000.0, 90.0)

    try:
        P_Pa = P_bar * 1e5
        rho_fluid = CP.PropsSI("D", "T", T_K_l, "P", P_Pa, liquid)
    except:
        st.error("Could not compute liquid density. Check fluid name and conditions.")
        rho_fluid = None

    V_t = st.number_input("Tank Volume (m^3):", 20.0, 10000.0, 100.0)
    V_i = st.number_input("Initial liquid volume (m³):", 0.0, V_t, 0.75* V_t) 
  
    



with col2:
    #T_K_g = st.number_input("Temperature of the gas (K):", 1.0, 1000.0, 90.0)
    #T_K_g_final = T_K_g - 10
    dont_estimate_temp = st.checkbox("Click if you know the gas temperature in the run tank. Otherwise it will be estimated from buffer tank conditions.")
    
    if dont_estimate_temp:
        T_K_g = st.number_input("Temperature of the gas (K):", 1.0, 1000.0, 250.0)
        T_K_g_final = T_K_g - 10

    else:
        # Buffer tank values
        T_K_buffer = st.number_input("Temperature in gas buffer tank (K):", 1.0, 1000.0, 293.0)
        P_buffer_bar = st.number_input("Pressure in gas buffer tank (bar):", 0.01, 500.0, 200.0)
        #D_RT = st.number_input("Diameter of the Run tank (in m)", 0.0,10.0, 3.0)
        #Area = np.pi * (D_RT/2)**2 

        # JT coefficient based on gas
        #if gas == 'N2':
         #   mu_JT = 0.2  # K/bar, positive — nitrogen cools on expansion
        #elif gas == 'He':
        #    mu_JT = -0.05  # K/bar, negative — helium warms on expansion
        
        # Estimate post-expansion temperature via JT
        #delta_T_JT = mu_JT * (P_bar - P_buffer_bar)
        #T_JT = T_K_buffer + delta_T_JT
        
        # Optional offset due to cryogenic tank cooling
        #cooling_offset = 10  # K
        #T_est = T_JT - cooling_offset
        
        #st.info(f"Estimated gas temperature after Joule-Thomson expansion and cold tank contact (-10 K): **{T_est:.2f} K**")
        
        # Override gas temperature input with estimated value
        #T_K_g = T_est


        # Step 1: get initial enthalpy
        h1 = CP.PropsSI('Hmass', 'T', T_K_buffer, 'P', P_buffer_bar*1e5, gas)  # [J/kg]

        # Step 2: compute final temperature at p2 with same h
        T2 = CP.PropsSI('T', 'Hmass', h1, 'P', P_bar*1e5, gas)
        cooling_offset = 10  # K
        T_K_g = T2 - cooling_offset
        T_K_g_final = T2 - cooling_offset
        

        st.info(f"Final temperature after isenthalpic expansion: {T_K_g_final:.2f} K")





    #V_i = st.number_input("Initial liquid volume (m^3):", 0.0, V_t, 500.0)
    #mdot = st.number_input("Mass flow rate of the liquid (kg/s):", 0.001, 100.0, 1.0)
    target = st.selectbox("Select whether you know the mass flow rate or the final volume of the liquid:", [
    "Mass Flow Rate (ṁ)",
    "Final Volume (m^3)"])
    if target == "Mass Flow Rate (ṁ)":
        mdot = st.number_input("Mass flow rate of the liquid (kg/s):", 0.001, 10000.0, 0.1)
        t = st.number_input("Duration (s):", 1.0, 500.0, 100.0)
        if rho_fluid:
            V_removed = mdot * t / rho_fluid
            V_f = V_i - V_removed
            if V_removed > V_i:
                st.warning("⚠️ Warning: The requested outflow exceeds the initial liquid volume!")
                V_f = 0.0
            st.info(f" The displaced liquid volume is **{V_removed:.2f} m³**. Therefore the final liquid volume is: **{V_f:.2f} m³**")
    if target == "Final Volume (m^3)":
        V_f = st.number_input("Final volume of liquid in tank (m^3):", 0.0, V_i, V_i/4)
        t = st.number_input("Duration (s):", 1.0, 500.0, 100.0)

        if rho_fluid is not None and rho_fluid > 0:
            V_removed = V_i - V_f
            mdot = V_removed * rho_fluid / t
            st.info(f" The displaced volume is **{V_removed:.2f} m³** . The estimated liquid mass flow rate is therefore: **{mdot:.2f} kg/s**")

   
    


    



         




# SI
P_pa = P_bar * 1e5

# Calculate properties

rho_0 = CP.PropsSI("D", "T", T_K_g, "P", P_pa, gas) # check density
rho_0_liquid = CP.PropsSI("D", "T", T_K_l, "P", P_pa, liquid) # check density
phase_liquid = CP.PhaseSI('P', P_pa, 'T', T_K_l, liquid)
phase_gases = CP.PhaseSI('P', P_pa, 'T', T_K_g, gas)
M = CP.PropsSI("M", gas)  # molar mass in kg/mol
 

phase_liquid = CP.PhaseSI('P', P_pa, 'T', T_K_l, liquid)


if phase_liquid not in ["liquid"]:
        st.warning(f"⚠️ Your chosen liquid is in {phase_liquid} phase at these conditions. Please adapt.")


if phase_gases not in ["gas", "supercritical_gas"]:
        st.warning(f"⚠️ Your chosen pressure gas is is in {phase_gases} phase at these conditions. Please adapt.")



# Main calculation



# Constants for nitrogen or helium
if gas == "N2":
    a = 0.1390  # Pa·m^6/mol^2
    b = 3.91e-5  # m^3/mol
elif gas == "He":
    a = 0.0346
    b = 2.34e-5

R = 8.314  # J/(mol·K)
 
# Initial and final gas volumes
V1 = V_t - V_i


with col1:
    pressurize_first = st.checkbox("Pressurize tank before outflow?", value=False)

    delta_n_pressurize = 0.0
    delta_m_pressurize = 0.0

    if pressurize_first:
        P_start_bar = st.number_input("Initial pressure before pressurization (bar):", 0.0, P_bar, 1.0)
        P_start_Pa = P_start_bar * 1e5

        try:
            rho_gas_start = CP.PropsSI("D", "T", T_K_g, "P", P_start_Pa, gas)
            n_start = (rho_gas_start * V1) / M
            # n1 = gas moles at P_bar, same V1 and T_K_g (already used later)
            n1_pressurized = (CP.PropsSI("D", "T", T_K_g, "P", P_pa, gas) * V1) / M
            delta_n_pressurize = n1_pressurized - n_start
            delta_m_pressurize = delta_n_pressurize * M
            st.success(f"Gas added for pressurization: {delta_m_pressurize:.3f} kg ({delta_n_pressurize:.1f} mol)")
        except:
            st.error("Could not compute gas density for initial pressure. Check temperature and pressure inputs.")


    if target == "Mass Flow Rate (ṁ)":
        V2 = V1 + (mdot * t) / rho_0_liquid
    else:
        V2 = V_t-V_f 

#col1.metric("V1", V1)
#col1.metric("Vrem", V_removed)

# Step 4: solve Van der Waals for n2 only
#def van_der_waals_n(V, p, T, a, b):
 #   def f(n):
  #      return (p + a * (n / V)**2) * (V - n * b) - n * R * T
   # n_guess = p * V / (R * T)  # ideal gas estimate
    #return fsolve(f, n_guess)[0]



# Test

# Assumption: the gas initially in the tank is at T_K_g (after JT), not cooled
rho_gas_initial = CP.PropsSI("D", "P", P_pa, "T", T_K_g_final-10, gas)  # kg/m³
n1 = (rho_gas_initial * V1) / M

# The added gas is cooled after inflow
rho_gas_added = CP.PropsSI("D", "P", P_pa, "T", T_K_g_final, gas)  # kg/m³
V_added = V2 - V1
n_added = (rho_gas_added * V_added) / M

# Total moles after inflow
n2 = n1 + n_added
delta_n = n2 - n1
delta_m = delta_n * M
gas_mdot = delta_m / t


if pressurize_first:
    # Total gas needed = pressurization + replacement
    delta_n_total = delta_n_pressurize + n_added
    delta_m_total = delta_m_pressurize + (n_added * M)
    #gas_mdot = delta_m_total / t
else:
    delta_n_total = n_added
    delta_m_total = n_added * M





#rho_gas = CP.PropsSI("D", "P", P_pa, "T", T_K_g, gas)  # kg/m³
##if T_K_g > (T_K_l + 10):
  #  rho_gas_final = CP.PropsSI("D", "P", P_pa, "T", T_K_g_final , gas)  # kg/m³
#else:
 #   rho_gas_final = CP.PropsSI("D", "P", P_pa, "T", T_K_g , gas)  # kg/m³

#n1 = (rho_gas * V1) / M
#n2 = (rho_gas * V2) / M
# n2 = (rho_gas_final * V2) / M


# Step 5: compute added moles
#delta_n = n2 - n1
#delta_V = V2-V1
#delta_m = delta_n * M  # [kg]

# Gas would need to inflow at this massflow to maintain constant pressure within the tank
#gas_mdot = rho_2 * delta_V/ t           # kg/s

#gas_mdot = delta_m / t


# --- Bottle Supply Calculation ---

V_n_tank = 50 * 1e-3  # m³ per bottle
T_N = 293  # K (room temperature)
P_N_i = 200 * 1e5  # Pa
P_N_f = 50 * 1e5   # Pa

# Molar mass (kg/mol) — already defined as M earlier, but redefined here for clarity
M = 28.0134e-3 if gas == "N2" else 4.0026e-3

# Densities at initial and final pressure in the gas supply bottle
rho_N_i = CP.PropsSI("D", "T", T_N, "P", P_N_i, gas)
rho_N_f = CP.PropsSI("D", "T", T_N, "P", P_N_f, gas)

# Moles per bottle (initial - final)
n_N_i = (rho_N_i * V_n_tank) / M
n_N_f = (rho_N_f * V_n_tank) / M
delta_n_N = n_N_i - n_N_f  # mol per bottle

# --- Total gas needed (already computed) ---
# delta_n_total, delta_m_total already exist

# Bottle count based on total moles
bottles = delta_n_total / delta_n_N

# --- Results Display ---

st.header("Results")
col1, col2 = st.columns(2)

col1.metric(f"Total added moles of {gas}", f"{delta_n_total:.1f} mol")
col1.metric(f"Total added mass of {gas}", f"{delta_m_total:.2f} kg")

if delta_n_total < 0:
    st.warning(f"⚠️ The number of gas moles decreased (∆n = {delta_n_total:.1f} mol). This suggests the gas volume is shrinking, which is unphysical if liquid is being removed. Please check your initial/final liquid volumes or flow direction.")

col2.metric("Required Gas mass inflow during outflow", f"{gas_mdot:.2f} kg/s")

if gas == 'N2':
    col2.metric("Required number of nitrogen bottles", f"{bottles:.2f} → {ceil(bottles):.0f} bottle(s)")
    with col2:
        st.info("Assumes nitrogen bottles of 50 L at 293 K (200 → 50 bar)")

if gas == 'He':
    col2.metric("Required number of helium bottles", f"{bottles:.2f} → {ceil(bottles):.0f} bottle(s)")
    with col2:
        st.info("Assumes helium bottles of 50 L at 293 K (200 → 50 bar)")
