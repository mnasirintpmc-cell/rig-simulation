import streamlit as st

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

# Simple, clean styling
st.markdown("""
<style>
    .nav-button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 1rem;
        font-size: 1.1rem;
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Main content
st.title("🏭 Rig Multi-P&ID Simulation")
st.markdown("### Interactive Process Simulation with Cross-System Reactions")

st.markdown("""
**Color Coding:**
- 🟢 **Green** = Fluid flowing (valve open + pressure)
- 🔵 **Light Blue** = Pressurized but no flow (valve closed)  
- ⚫ **Dark** = Empty/depressurized
- 🟣 **Purple** = Selected pipe for inspection
""")

# Simple navigation
cols = st.columns(5)

systems = [
    ("🔧 Mixing Area", "Mixing system with blending control", "app_mixing_p&id.py"),
    ("⚡ Pressure Supply", "Main pressure supply system", "app_pressure_supply_p&id.py"),
    ("🎮 DGS Simulation", "Dynamic Gas System simulation", "app_DGS_SIM.py"),
    ("🔄 Pressure Return", "Return line monitoring", "app_pressure_return_p&id.py"),
    ("🔒 Separation Seal", "Seal system monitoring", "app_separation_seal_p&id.py")
]

for col, (icon_name, description, page) in zip(cols, systems):
    with col:
        icon, name = icon_name.split(" ", 1)
        st.subheader(f"{icon} {name}")
        st.markdown(description)
        if st.button(f"Enter {name}", key=name, use_container_width=True):
            st.switch_page(f"pages/{page}")

# Key feature
st.markdown("---")
st.success("🎯 **Key Feature**: All 5 systems share valve states! Open/close a valve in any system → see the reaction propagate everywhere!")
