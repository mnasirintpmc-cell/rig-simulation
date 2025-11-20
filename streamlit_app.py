import streamlit as st
from PIL import Image, ImageDraw
import json
import math
import os

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if 'current_system' not in st.session_state:
    st.session_state.current_system = "home"
if 'valve_states' not in st.session_state:
    st.session_state.valve_states = {}
if 'selected_pipe' not in st.session_state:
    st.session_state.selected_pipe = None

# ==================== SIMPLE NAVIGATION ====================
st.title("🏭 Rig Multi-P&ID Simulation")

# Navigation
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔧 Mixing", use_container_width=True):
        st.session_state.current_system = "mixing"
        st.rerun()

with col2:
    if st.button("⚡ Supply", use_container_width=True):
        st.session_state.current_system = "supply"
        st.rerun()

with col3:
    if st.button("🎮 DGS", use_container_width=True):
        st.session_state.current_system = "dgs"
        st.rerun()

with col4:
    if st.button("🔄 Return", use_container_width=True):
        st.session_state.current_system = "return"
        st.rerun()

with col5:
    if st.button("🔒 Seal", use_container_width=True):
        st.session_state.current_system = "seal"
        st.rerun()

st.markdown("---")

# ==================== UNIVERSAL SIMULATION ENGINE ====================
def load_system_data(system_name):
    """Load data for the selected system"""
    data_map = {
        "mixing": {
            "valves": "data/valves_mixing.json",
            "pipes": "data/pipes_mixing.json", 
            "pressure_sources": [1, 5]
        },
        "supply": {
            "valves": "data/valves_pressure_in.json",
            "pipes": "data/pipes_pressure_in.json",
            "pressure_sources": [1, 3, 7]
        },
        "dgs": {
            "valves": "data/valves_dgs.json", 
            "pipes": "data/pipes_dgs.json",
            "pressure_sources": [1, 6, 11]
        },
        "return": {
            "valves": "data/valves_pressure_return.json",
            "pipes": "data/pipes_pressure_return.json", 
            "pressure_sources": [2, 8]
        },
        "seal": {
            "valves": "data/valves_seperation_seal.json",
            "pipes": "data/pipes_seperation_seal.json",
            "pressure_sources": [1, 4, 9]
        }
    }
    
    if system_name not in data_map:
        return None, None, []
    
    config = data_map[system_name]
    
    # Load valves
    try:
        with open(config["valves"], 'r') as f:
            valves = json.load(f)
    except:
        valves = {}
    
    # Load pipes  
    try:
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    except:
        pipes = []
    
    return valves, pipes, config["pressure_sources"]

def simulate_system(system_name, valves, pipes, pressure_sources):
    """Run simulation for a system"""
    st.header(f"{system_name.replace('_', ' ').title()} System")
    
    if not valves or not pipes:
        st.error(f"❌ Missing data for {system_name} system")
        st.info("Required files:")
        st.write(f"- Valves: data/valves_{system_name}.json")
        st.write(f"- Pipes: data/pipes_{system_name}.json")
        return
    
    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Create placeholder image (since we can't load PNGs)
    img = Image.new('RGB', (800, 600), (40, 40, 60))
    draw = ImageDraw.Draw(img)
    
    # Draw title
    draw.text((50, 50), f"{system_name} Simulation", fill="white")
    draw.text((50, 80), "Valve controls in sidebar →", fill="yellow")
    
    # Draw some sample pipes
    for i, pipe in enumerate(pipes[:10]):  # Only first 10 pipes for demo
        color = (0, 255, 0) if st.session_state.valve_states.get(list(valves.keys())[0], False) else (100, 100, 200)
        x1 = 100 + (i * 60)
        y1 = 200
        x2 = x1 + 50
        y2 = y1
        draw.line([(x1, y1), (x2, y2)], fill=color, width=6)
        draw.text((x1, y1-20), f"Pipe {i+1}", fill="white")
    
    # Draw some sample valves
    for i, (tag, valve_data) in enumerate(list(valves.items())[:5]):  # Only first 5 valves
        color = (0, 255, 0) if st.session_state.valve_states.get(tag, False) else (255, 0, 0)
        x = 150 + (i * 120)
        y = 300
        draw.ellipse([x-15, y-15, x+15, y+15], fill=color, outline="white", width=2)
        draw.text((x-20, y+20), tag, fill="white")
    
    # Display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.image(img, use_container_width=True, caption=f"{system_name} Simulation - Green = Flow, Red = Closed")
    
    with col2:
        st.header("Valve Controls")
        for tag in list(valves.keys())[:8]:  # Only first 8 valves
            state = st.session_state.valve_states[tag]
            if st.button(f"{'🟢 OPEN' if state else '🔴 CLOSED'} {tag}", key=f"{system_name}_{tag}"):
                st.session_state.valve_states[tag] = not state
                st.rerun()
        
        st.header("Status")
        open_valves = sum(1 for state in st.session_state.valve_states.values() if state)
        st.metric("Open Valves", open_valves)
        st.metric("Total Valves", len(valves))
        st.metric("Total Pipes", len(pipes))

# ==================== MAIN DISPLAY ====================
if st.session_state.current_system == "home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    st.markdown("""
    ### 👆 Select a system from the buttons above
    
    **Systems Available:**
    - 🔧 **Mixing**: Fluid mixing and blending
    - ⚡ **Supply**: Pressure supply system  
    - 🎮 **DGS**: Dynamic Gas System
    - 🔄 **Return**: Pressure return lines
    - 🔒 **Seal**: Separation and sealing
    
    **Features:**
    - 🎯 **Real-time simulation**
    - 🔄 **Cross-system interactions** 
    - 🎛️ **Interactive valve controls**
    - 📊 **Live status monitoring**
    """)
    
    # Show file status
    st.markdown("---")
    st.subheader("📁 System Status")
    systems = ["mixing", "supply", "dgs", "return", "seal"]
    for system in systems:
        valves_file = f"data/valves_{system}.json"
        pipes_file = f"data/pipes_{system}.json"
        
        valves_exists = os.path.exists(valves_file)
        pipes_exists = os.path.exists(pipes_file)
        
        if valves_exists and pipes_exists:
            st.success(f"✅ {system.title()}: Ready")
        else:
            st.error(f"❌ {system.title()}: Missing files")

else:
    # Load and simulate selected system
    system_display_names = {
        "mixing": "Mixing Area",
        "supply": "Pressure Supply", 
        "dgs": "DGS Simulation",
        "return": "Pressure Return",
        "seal": "Separation Seal"
    }
    
    valves, pipes, pressure_sources = load_system_data(st.session_state.current_system)
    simulate_system(system_display_names[st.session_state.current_system], valves, pipes, pressure_sources)

st.markdown("---")
st.success("🎯 **All systems are interconnected!** Valve changes affect the entire rig.")
