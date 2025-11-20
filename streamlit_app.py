import streamlit as st
import os

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

# Detect your actual folder structure
pages_folder = "pages" if os.path.exists("pages") else "page"

# Define systems with their actual file names
systems = [
    ("🔧 Mixing Area", "Mixing system with blending control", "app_mixing_p&id.py"),
    ("⚡ Pressure Supply", "Main pressure supply system", "app_pressure_supply_p&id.py"),
    ("🎮 DGS Simulation", "Dynamic Gas System simulation", "app_DGS_SIM.py"),
    ("🔄 Pressure Return", "Return line monitoring", "app_pressure_return_p&id.py"), 
    ("🔒 Separation Seal", "Seal system monitoring", "app_separation_seal_p&id.py")
]

# Check which systems actually exist
available_systems = []
for icon_name, description, page_file in systems:
    page_path = f"{pages_folder}/{page_file}"
    if os.path.exists(page_path):
        available_systems.append((icon_name, description, page_file))
    else:
        st.warning(f"⚠️ Missing: {page_path}")

# Main content
st.title("🏭 Rig Multi-P&ID Simulation")
st.markdown(f"### Found {len(available_systems)} available systems")

if available_systems:
    cols = st.columns(len(available_systems))
    
    for col, (icon_name, description, page) in zip(cols, available_systems):
        with col:
            icon, name = icon_name.split(" ", 1)
            st.subheader(f"{icon} {name}")
            st.markdown(description)
            if st.button(f"Enter {name}", key=name, use_container_width=True):
                st.switch_page(f"{pages_folder}/{page}")
else:
    st.error("❌ No systems found! Check your folder structure.")

st.markdown("---")
st.info(f"📁 Using folder: `{pages_folder}/`")
st.success("🎯 All systems share valve states - changes propagate everywhere!")
