should i change this version then import streamlit as st
import os
import json

st.set_page_config(
    page_title="Mixing Area P&ID Simulation",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .system-card {
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .system-ready {
        border-left-color: #28a745;
    }
    .system-missing {
        border-left-color: #ffc107;
    }
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
    .file-status {
        font-size: 0.85rem;
        color: #6c757d;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

def check_system_ready(system_name):
    """Check if all required files exist for a system"""
    # Fix: Your assets might be in root or assets folder
    png_paths = [
        f"assets/P&ID_{system_name}.png",
        f"P&ID_{system_name}.png",
        f"assets/{system_name}.png",
        f"{system_name}.png"
    ]
    
    valves_paths = [
        f"data/valves_{system_name}.json",
        f"valves_{system_name}.json",
        f"data/{system_name}_valves.json"
    ]
    
    pipes_paths = [
        f"data/pipes_{system_name}.json", 
        f"pipes_{system_name}.json",
        f"data/{system_name}_pipes.json"
    ]
    
    # Find existing files
    png_exists = any(os.path.exists(path) for path in png_paths)
    valves_exists = any(os.path.exists(path) for path in valves_paths)
    pipes_exists = any(os.path.exists(path) for path in pipes_paths)
    
    return png_exists and valves_exists and pipes_exists

def get_page_file(system_name):
    """Find the correct page file name"""
    page_variations = [
        f"page/{system_name}_p&id.py",
        f"page/{system_name}_pid.py",
        f"page/{system_name}.py",
        f"pages/{system_name}_p&id.py",
        f"pages/{system_name}_pid.py", 
        f"pages/{system_name}.py"
    ]
    
    for page_path in page_variations:
        if os.path.exists(page_path):
            return page_path
    
    return None

# System configurations - using your actual file names
systems = {
    "mixing": {
        "name": "Mixing P&ID", 
        "icon": "🏭",
        "description": "Main mixing process with material preparation and blending"
    },
    "pressure_in": {
        "name": "Pressure In P&ID", 
        "icon": "📊", 
        "description": "Main pressure supply system and distribution"
    },
    "dgs": {
        "name": "DGS P&ID", 
        "icon": "💨",
        "description": "Degassing system for gas removal and purification"
    },
    "pressure_return": {
        "name": "Pressure Return P&ID", 
        "icon": "↩️",
        "description": "Pressure return and recirculation system"
    },
    "seperation_seal": {  # Note: Using YOUR spelling "seperation"
        "name": "Separation Seal P&ID", 
        "icon": "⚗️",
        "description": "Separation and sealing system for product isolation"
    }
}

# Main header
st.markdown('<div class="main-header">🏭 Mixing Area P&ID Simulation</div>', unsafe_allow_html=True)

# Debug info (you can remove this later)
with st.expander("🔧 Debug File Structure"):
    st.write("**Current directory:**", os.listdir("."))
    if os.path.exists("page"):
        st.write("**Page folder contents:**", os.listdir("page"))
    if os.path.exists("assets"):
        st.write("**Assets folder contents:**", os.listdir("assets")) 
    if os.path.exists("data"):
        st.write("**Data folder contents:**", os.listdir("data"))

# Quick Navigation
st.markdown("## 🚀 Quick Navigation")
nav_cols = st.columns(5)

for i, (system_key, system_info) in enumerate(systems.items()):
    with nav_cols[i]:
        is_ready = check_system_ready(system_key)
        page_file = get_page_file(system_key)
        
        if page_file and is_ready:
            if st.button(
                f"{system_info['icon']}\n{system_info['name'].split()[0]}", 
                key=f"nav_{system_key}",
                use_container_width=True
            ):
                st.switch_page(page_file)
        else:
            st.button(
                f"{system_info['icon']}\n{system_info['name'].split()[0]}", 
                key=f"nav_{system_key}",
                use_container_width=True,
                disabled=True,
                help="System not fully configured"
            )

# System Status
st.markdown("---")
st.markdown("## 📊 System Status")

for system_key, system_info in enumerate(systems.items()):
    is_ready = check_system_ready(system_key)
    page_file = get_page_file(system_key)
    
    status_class = "system-ready" if (is_ready and page_file) else "system-missing"
    status_icon = "✅ Operational" if (is_ready and page_file) else "🚧 Setup Required"
    
    # File status
    png_found = any(os.path.exists(path) for path in [
        f"assets/P&ID_{system_key}.png", f"P&ID_{system_key}.png",
        f"assets/{system_key}.png", f"{system_key}.png"
    ])
    
    valves_found = any(os.path.exists(path) for path in [
        f"data/valves_{system_key}.json", f"valves_{system_key}.json",
        f"data/{system_key}_valves.json"
    ])
    
    pipes_found = any(os.path.exists(path) for path in [
        f"data/pipes_{system_key}.json", f"pipes_{system_key}.json", 
        f"data/{system_key}_pipes.json"
    ])
    
    png_status = "✅" if png_found else "❌"
    valves_status = "✅" if valves_found else "❌"
    pipes_status = "✅" if pipes_found else "❌"
    page_status = "✅" if page_file else "❌"
    
    st.markdown(f"""
    <div class="system-card {status_class}">
        <h3>{system_info['icon']} {system_info['name']}</h3>
        <p><strong>Status:</strong> {status_icon}</p>
        <p>{system_info['description']}</p>
        <p class="file-status">
        Page: {page_status} | P&ID: {png_status} | Valves: {valves_status} | Pipes: {pipes_status}
        </p>
    </div>
    """, unsafe_allow_html=True)

# Special case for Separation Seal (using your exact file names)
st.markdown("---")
st.markdown("## 🎯 Available Systems")

# Check specifically for your separation seal files
seperation_files = {
    "page": os.path.exists("page/seperation_seal_p&id.py"),
    "valves": os.path.exists("data/valves_seperation_seal.json"),
    "pipes": os.path.exists("data/pipes_seperation_seal.json"),
    "png": any(os.path.exists(path) for path in [
        "assets/P&ID_seperation_seal.png", "P&ID_seperation_seal.png",
        "assets/seperation_seal.png", "seperation_seal.png"
    ])
}

if seperation_files["page"]:
    st.success("✅ Separation Seal P&ID is available!")
    if st.button("⚗️ Go to Separation Seal P&ID", use_container_width=True):
        st.switch_page("page/seperation_seal_p&id.py")
else:
    st.warning("🚧 Separation Seal P&ID page not found")

# Show what separation seal files exist
st.write("**Separation Seal Files Found:**")
st.json(seperation_files)

# Instructions
st.markdown("---")
st.markdown("""
## 🔧 Setup Instructions

Based on your file structure, here's what you have:

### ✅ You Have:
- **Separation Seal P&ID** page: `page/seperation_seal_p&id.py`
- **Separation Seal pipes**: `data/pipes_seperation_seal.json`
- **Assets folder** with your P&ID images
- **Data folder** for valve/pipe configurations

### 📝 To Add More Systems:
1. Create page files in `page/` folder: `page/[system_name]_p&id.py`
2. Add valve files in `data/` folder: `data/valves_[system_name].json`  
3. Add pipe files in `data/` folder: `data/pipes_[system_name].json`
4. Add background images in `assets/` folder: `assets/P&ID_[system_name].png`

### 🎯 Next Steps:
1. **Click the Separation Seal button above** to test your working system
2. **Add the other 4 systems** following the same pattern
3. **Update valve/pipe JSON files** with your actual equipment data
""")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🏭 Mixing Area P&ID Simulation • Adapted for Your File Structure"
    "</div>", 
    unsafe_allow_html=True
)
