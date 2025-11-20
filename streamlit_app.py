import streamlit as st

st.set_page_config(page_title="Rig Simulation", layout="wide")

st.title("🏭 Rig Simulation Dashboard")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔧 Mixing", use_container_width=True):
        st.switch_page("app_mixing_p&id.py")

with col2:
    if st.button("⚡ Supply", use_container_width=True):
        st.switch_page("app_pressure_supply_p&id.py")

with col3:
    if st.button("🎮 DGS", use_container_width=True):
        st.switch_page("app_DGS_SIM.py")

with col4:
    if st.button("🔄 Return", use_container_width=True):
        st.switch_page("app_pressure_return_p&id.py")

with col5:
    if st.button("🔒 Seal", use_container_width=True):
        st.switch_page("app_separation_seal_p&id.py")

st.success("Valve changes affect all interconnected systems!")
