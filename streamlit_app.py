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

# ==================== SIMULATION ENGINE ====================
def load_system_data(system_name):
    """Load data for selected system"""
    system_map = {
        "mixing": {
            "valves": "data/valves_mixing.json", 
            "pipes": "data/pipes_mixing.json", 
            "png": "assets/p&id_mixing.png"  # ← Try this path first
        },
        "supply": {
            "valves": "data/valves_pressure_in.json", 
            "pipes": "data/pipes_pressure_in.json", 
            "png": "assets/p&id_pressure_in.png"
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
            "valves": "data/valves_seperation_seal.json", 
            "pipes": "data/pipes_seperation_seal.json", 
            "png": "assets/p&id_seperation_seal.png"
        }
    }
    
    if system_name not in system_map:
        return None, None, None
    
    config = system_map[system_name]
    
    # Load valves
    try:
        with open(config["valves"], 'r') as f:
            valves = json.load(f)
    except Exception as e:
        st.error(f"❌ Cannot load valves: {e}")
        valves = {}
    
    # Load pipes
    try:
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    except Exception as e:
        st.error(f"❌ Cannot load pipes: {e}")
        pipes = []
    
    # Find PNG file - try multiple locations
    png_path = config["png"]
    if not os.path.exists(png_path):
        # Try alternative locations
        alt_paths = [
            png_path,
            png_path.replace("assets/", ""),  # Try root directory
            png_path.replace("p&id_", "P&ID_"),  # Try capital P
            f"page/{png_path}",  # Try in page folder
            f"../{png_path}"  # Try one level up
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                png_path = alt_path
                break
        else:
            png_path = None
    
    return valves, pipes, png_path

def render_pid_with_overlay(valves, pipes, png_path, system_name):
    """Render P&ID with valve and pipe overlays"""
    try:
        # Load background P&ID
        img = Image.open(png_path).convert("RGBA")
        st.sidebar.success(f"✅ Loaded P&ID: {os.path.basename(png_path)}")
    except Exception as e:
        st.error(f"❌ Cannot load P&ID image: {e}")
        # Create placeholder
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"P&ID Not Found: {png_path}", fill="white")
        return img.convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    # Draw pipes with color coding
    for i, pipe in enumerate(pipes):
        # Check if pipe has flow (simple logic - if any valve is open)
        has_flow = any(st.session_state.valve_states.get(tag, False) for tag in valves)
        
        if i == st.session_state.selected_pipe:
            color = (180, 0, 255)  # Purple for selected
            width = 8
        elif has_flow:
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
        
        # Draw valve circle
        draw.ellipse([x-10, y-10, x+10, y+10], fill=color, outline="white", width=2)
        
        # Draw valve label
        draw.text((x+12, y-10), tag, fill="white", stroke_fill="black", stroke_width=1)
    
    return img.convert("RGB")

def run_simulation(system_name):
    """Run the simulation for selected system"""
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
        st.error("❌ Cannot run simulation - missing valve or pipe data")
        st.info("Required files:")
        st.write(f"- valves: data/valves_{system_name}.json")
        st.write(f"- pipes: data/pipes_{system_name}.json")
        st.write(f"- png: assets/p&id_{system_name}.png")
        return
    
    if not png_path:
        st.error(f"❌ P&ID image not found for {system_name}")
        st.info("Looking for: assets/p&id_{system_name}.png")
        return
    
    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Valve controls in sidebar
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
        
        # Pipe selection
        st.header("📏 Pipe Selection")
        if st.button("Unselect Pipe", key="unselect"):
            st.session_state.selected_pipe = None
            st.rerun()
        
        for i in range(min(10, len(pipes))):  # Show first 10 pipes
            is_selected = i == st.session_state.selected_pipe
            label = f"🔷 Pipe {i+1}" if is_selected else f"Pipe {i+1}"
            if st.button(label, key=f"pipe_{i}"):
                st.session_state.selected_pipe = i
                st.rerun()
    
    # Render and display P&ID
    col1, col2 = st.columns([3, 1])
    
    with col1:
        rendered_image = render_pid_with_overlay(valves, pipes, png_path, display_names[system_name])
        st.image(rendered_image, use_container_width=True, 
                caption=f"{display_names[system_name]} - Green=Flow, Red=Closed Valve")
    
    with col2:
        st.header("🎯 Legend")
        st.write("🟢 **Green pipes**: Fluid flowing")
        st.write("🔵 **Blue pipes**: No flow")
        st.write("🟣 **Purple pipes**: Selected")
        st.write("🟢 **Green valves**: Open")
        st.write("🔴 **Red valves**: Closed")
        st.write("---")
        st.info("💡 **Click valves** in sidebar to open/close them")
        st.info("💡 **Click pipes** in sidebar to select them")

# ==================== MAIN DISPLAY ====================
if st.session_state.current_system == "home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    st.markdown("👆 **Select a system from the buttons above to see the actual P&ID diagrams**")
    
    # File status
    st.markdown("---")
    st.subheader("📁 System Status")
    
    systems = ["mixing", "supply", "dgs", "return", "seal"]
    for system in systems:
        valves_file = f"data/valves_{system}.json"
        pipes_file = f"data/pipes_{system}.json"
        png_file = f"assets/p&id_{system}.png"
        
        valves_ok = os.path.exists(valves_file)
        pipes_ok = os.path.exists(pipes_file)
        png_ok = os.path.exists(png_file)
        
        if valves_ok and pipes_ok and png_ok:
            st.success(f"✅ {system.title()}: READY")
        elif valves_ok and pipes_ok:
            st.warning(f"⚠️ {system.title()}: Data OK, PNG missing")
        else:
            st.error(f"❌ {system.title()}: Missing files")

else:
    run_simulation(st.session_state.current_system)

st.markdown("---")
st.success("🎯 **Interactive P&ID Simulation** - Click valves to see real-time flow changes!")
