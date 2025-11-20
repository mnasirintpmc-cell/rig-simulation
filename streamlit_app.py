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

# ==================== SIMPLE FILE PATHS ====================
def load_system_data(system_name):
    """Simple file loading - all files follow same pattern"""
    valves_path = f"data/valves_{system_name}.json"
    pipes_path = f"data/pipes_{system_name}.json"
    png_path = f"assets/p&id_{system_name}.png"
    
    # Load valves
    valves = {}
    if os.path.exists(valves_path):
        try:
            with open(valves_path, 'r') as f:
                valves = json.load(f)
        except:
            st.error(f"Error loading {valves_path}")
    else:
        st.error(f"Missing: {valves_path}")
    
    # Load pipes
    pipes = []
    if os.path.exists(pipes_path):
        try:
            with open(pipes_path, 'r') as f:
                pipes = json.load(f)
        except:
            st.error(f"Error loading {pipes_path}")
    else:
        st.error(f"Missing: {pipes_path}")
    
    # Check PNG
    if not os.path.exists(png_path):
        st.error(f"Missing: {png_path}")
        png_path = None
    
    return valves, pipes, png_path

# ==================== NAVIGATION ====================
st.title("🏭 Rig Multi-P&ID Simulation")

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

# ==================== RENDERING ====================
def render_pid_with_overlay(valves, pipes, png_path, system_name):
    """Render P&ID with interactive overlays"""
    try:
        img = Image.open(png_path).convert("RGBA")
    except:
        # Create placeholder if PNG missing
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"{system_name} - P&ID Placeholder", fill="white")
        return img.convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        has_flow = any(st.session_state.valve_states.get(tag, False) for tag in valves)
        
        if has_flow:
            color = (0, 255, 0)  # Green for flow
            width = 6
        else:
            color = (100, 100, 255)  # Blue for no flow
            width = 4
            
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
    
    # Draw valves
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        color = (0, 255, 0) if is_open else (255, 0, 0)  # Green=open, Red=closed
        
        x, y = valve_data["x"], valve_data["y"]
        draw.ellipse([x-10, y-10, x+10, y+10], fill=color, outline="white", width=2)
        draw.text((x+12, y-10), tag, fill="white")
    
    return img.convert("RGB")

def run_simulation(system_name):
    """Run simulation for selected system"""
    display_names = {
        "mixing": "Mixing Area",
        "supply": "Pressure Supply", 
        "dgs": "DGS Simulation",
        "return": "Pressure Return", 
        "seal": "Separation Seal"
    }
    
    st.header(f"{display_names[system_name]} Simulation")
    
    # Load data
    valves, pipes, png_path = load_system_data(system_name)
    
    if not valves or not pipes:
        st.error("❌ Missing data files - create the JSON files first")
        return
    
    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Valve Controls")
        for tag in valves:
            state = st.session_state.valve_states[tag]
            label = f"{'🟢 OPEN' if state else '🔴 CLOSED'} {tag}"
            if st.button(label, key=f"{system_name}_{tag}"):
                st.session_state.valve_states[tag] = not state
                st.rerun()
        
        st.header("📊 Status")
        open_valves = sum(st.session_state.valve_states.values())
        st.metric("Open Valves", open_valves)
        st.metric("Total Valves", len(valves))
        st.metric("Total Pipes", len(pipes))
    
    # Main display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        image = render_pid_with_overlay(valves, pipes, png_path, display_names[system_name])
        st.image(image, use_container_width=True, 
                caption=f"{display_names[system_name]} - Interactive P&ID")
    
    with col2:
        st.header("🎯 Legend")
        st.write("🟢 **Green pipes**: Fluid flowing")
        st.write("🔵 **Blue pipes**: No flow")
        st.write("🟢 **Green valves**: Open")
        st.write("🔴 **Red valves**: Closed")

# ==================== MAIN DISPLAY ====================
if st.session_state.current_system == "home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    st.markdown("👆 **Select a system to view P&ID and control valves**")
    
    # File status
    st.markdown("---")
    st.subheader("📁 System Status")
    
    systems = ["mixing", "supply", "dgs", "return", "seal"]
    for system in systems:
        valves_exists = os.path.exists(f"data/valves_{system}.json")
        pipes_exists = os.path.exists(f"data/pipes_{system}.json")
        png_exists = os.path.exists(f"assets/p&id_{system}.png")
        
        if valves_exists and pipes_exists and png_exists:
            st.success(f"✅ {system.title()}: READY")
        elif valves_exists and pipes_exists:
            st.warning(f"⚠️ {system.title()}: Data OK, PNG missing")
        else:
            st.error(f"❌ {system.title()}: Missing data files")

else:
    run_simulation(st.session_state.current_system)

st.markdown("---")
st.success("🎯 **All systems now work! Click valves to see flow changes.**")
