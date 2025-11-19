import streamlit as st
import os

st.set_page_config(
    page_title="Mixing Area P&ID Simulation",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check which systems have files
def check_system_ready(system_name):
    png_exists = os.path.exists(f"P&ID_{system_name}.png")
    valves_exists = os.path.exists(f"valves_{system_name}.json")
    pipes_exists = os.path.exists(f"pipes_{system_name}.json")
    return png_exists and valves_exists and pipes_exists

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .system-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
    }
    .system-ready {
        background-color: #e8f5e8;
        border-left-color: #4caf50;
    }
    .system-missing {
        background-color: #fff3e0;
        border-left-color: #ff9800;
    }
    .nav-button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 1rem;
        font-size: 1.1rem;
    }
    .file-status {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🏭 Mixing Area P&ID Simulation</div>', unsafe_allow_html=True)

# Check system readiness
systems = {
    "mixing": {"name": "Mixing P&ID", "icon": "🏭", "ready": check_system_ready("mixing")},
    "pressure_in": {"name": "Pressure In P&ID", "icon": "📊", "ready": check_system_ready("pressure_in")},
    "dgs": {"name": "DGS P&ID", "icon": "💨", "ready": check_system_ready("dgs")},
    "pressure_return": {"name": "Pressure Return P&ID", "icon": "↩️", "ready": check_system_ready("pressure_return")},
    "separation_seal": {"name": "Separation Seal P&ID", "icon": "⚗️", "ready": check_system_ready("separation_seal")},
}

# Quick navigation
st.markdown("## 🚀 Quick Navigation")
cols = st.columns(5)

for i, (system_key, system_info) in enumerate(systems.items()):
    with cols[i]:
        button_text = f"{system_info['icon']}\n{system_info['name'].split()[0]}"
        if system_info['ready']:
            if st.button(button_text, key=f"nav_{system_key}", use_container_width=True, type="primary"):
                st.switch_page(f"pages/{i+1}_{system_info['icon']}_{system_info['name'].replace(' ', '_')}.py")
        else:
            st.button(button_text, key=f"nav_{system_key}", use_container_width=True, disabled=True)

# System Status
st.markdown("---")
st.markdown("## 📊 System Status")

for system_key, system_info in systems.items():
    status_class = "system-ready" if system_info['ready'] else "system-missing"
    status_icon = "✅" if system_info['ready'] else "🚧"
    status_text = "Ready" if system_info['ready'] else "Files Missing"
    
    st.markdown(f"""
    <div class="system-card {status_class}">
        <h3>{system_info['icon']} {system_info['name']} {status_icon}</h3>
        <p><strong>Status:</strong> {status_text}</p>
        <p class="file-status">
        P&ID: {'✅' if os.path.exists(f'P&ID_{system_key}.png') else '❌'} | 
        Valves: {'✅' if os.path.exists(f'valves_{system_key}.json') else '❌'} | 
        Pipes: {'✅' if os.path.exists(f'pipes_{system_key}.json') else '❌'}
        </p>
    </div>
    """, unsafe_allow_html=True)

# Instructions
st.markdown("---")
st.markdown("""
### 🎯 How to Add New Systems

For each P&ID system, create these 3 files:

1. **`P&ID_[system].png`** - Background P&ID image
2. **`valves_[system].json`** - Valve definitions with coordinates
3. **`pipes_[system].json`** - Pipe definitions with coordinates

**Example for Pressure In system:**
- `P&ID_pressure_in.png`
- `valves_pressure_in.json` 
- `pipes_pressure_in.json`

### 🔧 File Templates

**valves_pressure_in.json:**
```json
{
  "V-PI-101": {"x": 100, "y": 200, "state": false},
  "V-PI-102": {"x": 300, "y": 150, "state": false}
}
