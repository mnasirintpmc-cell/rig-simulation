# streamlit_app.py
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

# ==================== CORRECT FILE MAPPING ====================
def get_system_files(system_name):
    """Get the correct file names for each system - MATCHING YOUR ACTUAL FILES"""
    file_map = {
        "mixing": {
            "valves": "data/valves_mixing.json",
            "pipes": "data/pipes_mixing.json", 
            "png": "assets/p&id_mixing.png"
        },
        "supply": {
            "valves": "data/valves_pressure_in.json",      # Your actual file
            "pipes": "data/pipes_pressure_in.json",        # Your actual file
            "png": "assets/p&id_pressure_in.png"           # Your actual file
        },
        "dgs": {
            "valves": "data/valves_dgs.json",
            "pipes": "data/pipes_dgs.json",
            "png": "assets/p&id_dgs.png"
        },
        "return": {
            "valves": "data/valves_pressure_return.json",
            "pipes": "data/pipes_pressure_return.json",
            "png": "assets/p&id_pressure_return.png"
        },
        "seal": {
            "valves": "data/valves_separtaion_seal.json",  # Your actual spelling
            "pipes": "data/pipes_separtaion_seal.json",    # Your actual spelling
            "png": "assets/p&id_separtaion_seal.png"       # Your actual spelling
        }
    }
    
    if system_name not in file_map:
        return None, None, None
    
    config = file_map[system_name]
    return config["valves"], config["pipes"], config["png"]

def load_system_data(system_name):
    """Load data using correct file names"""
    valves_path, pipes_path, png_path = get_system_files(system_name)
    
    # Load valves
    valves = {}
    if valves_path and os.path.exists(valves_path):
        try:
            with open(valves_path, 'r') as f:
                valves = json.load(f)
            st.sidebar.success(f"✅ Valves: {os.path.basename(valves_path)}")
        except Exception as e:
            st.error(f"❌ Error loading valves: {e}")
    else:
        st.error(f"❌ Missing: {valves_path}")
    
    # Load pipes
    pipes = []
    if pipes_path and os.path.exists(pipes_path):
        try:
            with open(pipes_path, 'r') as f:
                pipes = json.load(f)
            st.sidebar.success(f"✅ Pipes: {os.path.basename(pipes_path)}")
        except Exception as e:
            st.error(f"❌ Error loading pipes: {e}")
    else:
        st.error(f"❌ Missing: {pipes_path}")
    
    # Check PNG
    if not png_path or not os.path.exists(png_path):
        st.error(f"❌ Missing: {png_path}")
        png_path = None
    else:
        st.sidebar.success(f"✅ P&ID: {os.path.basename(png_path)}")
    
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
    except Exception as e:
        st.error(f"❌ Cannot load P&ID: {e}")
        # Create placeholder
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"P&ID Not Found", fill="white")
        draw.text((50, 80), f"Path: {png_path}", fill="yellow")
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
        color = (0, 255, 0) if is_open else (255, 0, 0)
        
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
        st.error("❌ Cannot run - missing JSON data files")
        st.info("Please check that all JSON files exist in the data/ folder")
        return
    
    if not png_path:
        st.error(f"❌ P&ID image not found")
        st.info("Please check that the PNG file exists in the assets/ folder")
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
        
        # Clear button
        if st.button("🔄 Clear All Valves", use_container_width=True):
            for tag in valves:
                st.session_state.valve_states[tag] = False
            st.rerun()
    
    # Main display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        image = render_pid_with_overlay(valves, pipes, png_path, display_names[system_name])
        st.image(image, use_container_width=True, 
                caption=f"{display_names[system_name]} - Green=Flow, Red=Closed")
    
    with col2:
        st.header("🎯 Legend")
        st.write("🟢 **Green pipes**: Fluid flowing")
        st.write("🔵 **Blue pipes**: No flow")
        st.write("🟢 **Green valves**: Open")
        st.write("🔴 **Red valves**: Closed")
        st.write("---")
        st.info("💡 **Click valves** in sidebar to open/close them")
        st.info("💡 **Watch pipes** change color when valves open")

# ==================== MAIN DISPLAY ====================
if st.session_state.current_system == "home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    st.markdown("👆 **Select a system from the buttons above to view P&ID diagrams and control valves**")
    
    # File status with ACTUAL file names
    st.markdown("---")
    st.subheader("📁 System Status")
    
    systems = [
        ("mixing", "Mixing Area"),
        ("supply", "Pressure Supply"), 
        ("dgs", "DGS Simulation"),
        ("return", "Pressure Return"), 
        ("seal", "Separation Seal")
    ]
    
    all_systems_ready = True
    
    for system, display_name in systems:
        valves_path, pipes_path, png_path = get_system_files(system)
        
        valves_exists = valves_path and os.path.exists(valves_path)
        pipes_exists = pipes_path and os.path.exists(pipes_path)
        png_exists = png_path and os.path.exists(png_path)
        
        status = "✅ READY" if all([valves_exists, pipes_exists, png_exists]) else "❌ INCOMPLETE"
        
        if not all([valves_exists, pipes_exists, png_exists]):
            all_systems_ready = False
        
        st.write(f"**{display_name}**: {status}")
        
        if valves_exists:
            st.write(f"  - Valves: ✅ {os.path.basename(valves_path)}")
        else:
            st.write(f"  - Valves: ❌ {valves_path}")
            
        if pipes_exists:
            st.write(f"  - Pipes: ✅ {os.path.basename(pipes_path)}")
        else:
            st.write(f"  - Pipes: ❌ {pipes_path}")
            
        if png_exists:
            st.write(f"  - P&ID: ✅ {os.path.basename(png_path)}")
        else:
            st.write(f"  - P&ID: ❌ {png_path}")
    
    if all_systems_ready:
        st.success("🎉 All systems are ready! Click any system above to start simulating.")
    else:
        st.warning("⚠️ Some systems are missing files. Check the file paths above.")

else:
    run_simulation(st.session_state.current_system)

st.markdown("---")
st.success("🎯 **Interactive P&ID Simulation** - Real-time valve control and flow visualization!")
