import streamlit as st
import os

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if 'current_system' not in st.session_state:
    st.session_state.current_system = None

# Main navigation
st.title("🏭 Rig Multi-P&ID Simulation")
st.markdown("### Choose a system to simulate")

# Navigation buttons
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

# Display selected system
st.markdown("---")

if st.session_state.current_system:
    system_name = {
        "mixing": "Mixing Area",
        "supply": "Pressure Supply", 
        "dgs": "DGS Simulation",
        "return": "Pressure Return",
        "seal": "Separation Seal"
    }[st.session_state.current_system]
    
    st.success(f"🎯 Selected: {system_name}")
    
    # Show file status
    expected_file = f"app_{st.session_state.current_system}_p&id.py"
    if st.session_state.current_system == "dgs":
        expected_file = "app_DGS_SIM.py"
    elif st.session_state.current_system == "seal":
        expected_file = "app_separation_seal_p&id.py"
    
    if os.path.exists(expected_file):
        st.success(f"✅ File exists: `{expected_file}`")
        st.info(f"💡 To run this system, use: `streamlit run {expected_file}`")
    else:
        st.error(f"❌ File not found: `{expected_file}`")
        
    # Show what files actually exist
    st.write("**Available Python files:**")
    py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'streamlit_app.py']
    for py_file in py_files:
        st.write(f"- `{py_file}`")
else:
    st.info("👆 Select a system above to get started")

st.markdown("---")
st.success("🎯 All systems share valve states - changes propagate everywhere!")
