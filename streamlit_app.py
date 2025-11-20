import streamlit as st
import os

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Rig Multi-P&ID Simulation")
st.markdown("### Choose a system to simulate")

# Your apps are in the 'page' folder - use the correct path
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔧 Mixing Area", use_container_width=True):
        st.switch_page("page/app_mixing_p&id.py")

with col2:
    if st.button("⚡ Pressure Supply", use_container_width=True):
        st.switch_page("page/app_pressure_supply_p&id.py")

with col3:
    if st.button("🎮 DGS Simulation", use_container_width=True):
        st.switch_page("page/app_DGS_SIM.py")

with col4:
    if st.button("🔄 Pressure Return", use_container_width=True):
        st.switch_page("page/app_pressure_return_p&id.py")

with col5:
    if st.button("🔒 Separation Seal", use_container_width=True):
        st.switch_page("page/app_separation_seal_p&id.py")

# Show file verification
st.markdown("---")
st.write("**File Verification:**")
if os.path.exists("page"):
    files = os.listdir("page")
    st.success(f"✅ 'page' folder exists with {len(files)} files")
    for file in files:
        if file.endswith('.py'):
            st.write(f"- ✅ `{file}`")
else:
    st.error("❌ 'page' folder not found!")

st.markdown("---")
st.success("🎯 All systems share valve states - changes propagate everywhere!")
