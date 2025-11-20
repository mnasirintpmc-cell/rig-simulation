# home.py
import streamlit as st

st.set_page_config(page_title="Rig Simulation", layout="wide")
st.title("Rig Multi-P&ID Simulation")
st.markdown("### Choose a system to simulate pressurization and see cross-reaction")

cols = st.columns(5)
systems = [
    ("Mixing Area", "app_mixing.py"),
    ("Pressure In", "app_pressure_in.py"),
    ("DGS", "app_dgs.py"),
    ("Pressure Return", "app_pressure_return.py"),
    ("Separation Seal", "app_separation_seal.py")
]

for col, (name, file) in zip(cols, systems):
    with col:
        if st.button(name, use_container_width=True):
            st.switch_page(file)

st.success("All 5 systems share the same valves & pipes → Open a valve here → see reaction everywhere!")
