import streamlit as st

st.set_page_config(page_title="Rig Simulation", layout="wide")
st.title("Rig Multi-P&ID Simulation")
st.markdown("### Choose a system to simulate pressurization and see cross-reaction")

cols = st.columns(5)
systems = [
    ("Mixing Area", "app_mixing_p&id.py"),
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

st.markdown("---")
st.subheader("🎯 Dynamic Simulation Features")
st.markdown("""
- **Zero Hard-Coding**: Automatic valve-pipe relationship detection
- **Universal Template**: Same code works for all P&IDs
- **Real-time Propagation**: Pressure flows through connected systems
- **Visual Feedback**: Clear color coding for flow states
- **Interactive Selection**: Click pipes for inspection
""")
