import streamlit as st

st.set_page_config(
    page_title="Rig Simulation Dashboard", 
    page_icon="🏭",
    layout="wide"
)

# Use session state to simulate navigation
if 'current_system' not in st.session_state:
    st.session_state.current_system = None

st.title("🏭 Rig Multi-P&ID Simulation")
st.markdown("### Choose a system to simulate")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔧 Mixing Area", use_container_width=True):
        st.session_state.current_system = "mixing"

with col2:
    if st.button("⚡ Pressure Supply", use_container_width=True):
        st.session_state.current_system = "supply"

with col3:
    if st.button("🎮 DGS Simulation", use_container_width=True):
        st.session_state.current_system = "dgs"

with col4:
    if st.button("🔄 Pressure Return", use_container_width=True):
        st.session_state.current_system = "return"

with col5:
    if st.button("🔒 Separation Seal", use_container_width=True):
        st.session_state.current_system = "seal"

# Show instructions based on selection
st.markdown("---")
if st.session_state.current_system:
    system_info = {
        "mixing": ("app_mixing_p&id.py", "Mixing Area"),
        "supply": ("app_pressure_supply_p&id.py", "Pressure Supply"),
        "dgs": ("app_DGS_SIM.py", "DGS Simulation"), 
        "return": ("app_pressure_return_p&id.py", "Pressure Return"),
        "seal": ("app_separation_seal_p&id.py", "Separation Seal")
    }
    
    file_name, display_name = system_info[st.session_state.current_system]
    st.success(f"🎯 Selected: {display_name}")
    st.info(f"💡 To run this system, use this command:")
    st.code(f"streamlit run page/{file_name}")
    st.warning("⚠️ Copy and paste the command above to run the individual system")
else:
    st.info("👆 Select a system above to get started")

st.markdown("---")
st.success("🎯 All systems share valve states - changes propagate everywhere!")
