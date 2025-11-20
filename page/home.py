import streamlit as st

st.set_page_config(page_title="Rig Simulation", layout="wide")
st.title("Rig Multi-P&ID Simulation")
st.markdown("### Choose a system to simulate pressurization and see cross-reaction")

cols = st.columns(5)
systems = [
    ("Mixing P&ID", "app_mixing_p&id.py"),
    ("Pressure Supply", "app_pressure_supply_p&id.py"),
    ("DGS Simulation", "app_DGS_SIM.py"),
    ("Pressure Return", "app_pressure_return_p&id.py"),
    ("Separation Seal", "app_seperation_seal_p&id.py")
]

for col, (name, file) in zip(cols, systems):
    with col:
        if st.button(name, use_container_width=True):
            st.switch_page(file)

st.success("All 5 systems share the same valves & pipes → Open a valve here → see reaction everywhere!")

# Additional information section
st.markdown("---")
st.subheader("System Overview")
st.markdown("""
This rig simulation consists of 5 interconnected systems:

- **Mixing P&ID**: Fluid mixing and blending control
- **Pressure Supply**: Main pressure supply system  
- **DGS Simulation**: Dynamic Gas System simulation
- **Pressure Return**: Return line monitoring system
- **Separation Seal**: Seal system monitoring and control

**Key Feature**: Changes in one system automatically affect all connected systems!
""")
