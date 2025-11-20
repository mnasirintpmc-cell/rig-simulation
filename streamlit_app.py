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

# ==================== DYNAMIC FILE DISCOVERY ====================
def find_system_files(system_name):
    """Dynamically find files for any system"""
    
    # Possible file name variations
    valves_patterns = [
        f"data/valves_{system_name}.json",
        f"data/valves_{system_name}_p&id.json",
        f"valves_{system_name}.json",
        f"page/valves_{system_name}.json"
    ]
    
    pipes_patterns = [
        f"data/pipes_{system_name}.json", 
        f"data/pipes_{system_name}_p&id.json",
        f"pipes_{system_name}.json",
        f"page/pipes_{system_name}.json"
    ]
    
    png_patterns = [
        f"assets/p&id_{system_name}.png",
        f"assets/{system_name}.png", 
        f"p&id_{system_name}.png",
        f"{system_name}.png",
        f"assets/p&id_{system_name}_p&id.png"
    ]
    
    # Special cases for system name variations
    if system_name == "supply":
        png_patterns.extend([
            "assets/p&id_pressure_in.png",
            "assets/pressure_in.png"
        ])
        valves_patterns.extend([
            "data/valves_pressure_in.json",
            "data/valves_pressure_supply.json"
        ])
        pipes_patterns.extend([
            "data/pipes_pressure_in.json", 
            "data/pipes_pressure_supply.json"
        ])
    elif system_name == "seal":
        png_patterns.extend([
            "assets/p&id_seperation_seal.png",  # Your spelling
            "assets/seperation_seal.png"
        ])
    
    # Find files
    valves_path = None
    for pattern in valves_patterns:
        if os.path.exists(pattern):
            valves_path = pattern
            break
    
    pipes_path = None
    for pattern in pipes_patterns:
        if os.path.exists(pattern):
            pipes_path = pattern
            break
    
    png_path = None
    for pattern in png_patterns:
        if os.path.exists(pattern):
            png_path = pattern
            break
    
    return valves_path, pipes_path, png_path

def load_system_data(system_name):
    """Load data using discovered file paths"""
    valves_path, pipes_path, png_path = find_system_files(system_name)
    
    # Load valves
    valves = {}
    if valves_path:
        try:
            with open(valves_path, 'r') as f:
                valves = json.load(f)
            st.sidebar.success(f"✅ Valves: {os.path.basename(valves_path)}")
        except Exception as e:
            st.error(f"❌ Error loading valves: {e}")
    else:
        st.error(f"❌ No valves file found for {system_name}")
    
    # Load pipes
    pipes = []
    if pipes_path:
        try:
            with open(pipes_path, 'r') as f:
                pipes = json.load(f)
            st.sidebar.success(f"✅ Pipes: {os.path.basename(pipes_path)}")
        except Exception as e:
            st.error(f"❌ Error loading pipes: {e}")
    else:
        st.error(f"❌ No pipes file found for {system_name}")
    
    # Check PNG
    if not png_path:
        st.error(f"❌ No P&ID image found for {system_name}")
    
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
        st.sidebar.success(f"✅ P&ID: {os.path.basename(png_path)}")
    except Exception as e:
        st.error(f"❌ Cannot load P&ID: {e}")
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"P&ID Not Found", fill="white")
        draw.text((50, 80), f"Looking for: {png_path}", fill="yellow")
        return img.convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        has_flow = any(st.session_state.valve_states.get(tag, False) for tag in valves)
        
        if i == st.session_state.selected_pipe:
            color = (180, 0, 255)
            width = 8
        elif has_flow:
            color = (0, 255, 0)
            width = 6
        else:
            color = (100, 100, 255)
            width = 4
            
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
    
    # Draw valves
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        color = (0, 255, 0) if is_open else (255, 0, 0)
        
        x, y = valve_data["x"], valve_data["y"]
        draw.ellipse([x-10, y-10, x+10, y+10], fill=color, outline="white", width=2)
        draw.text((x+12, y-10), tag, fill="white", stroke_fill="black", stroke_width=1)
    
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
    
    if not valves or not pipes or not png_path:
        st.error("❌ Cannot run - missing files")
        st.info("Looking for:")
        st.write(f"- Valves: valves_{system_name}.json")
        st.write(f"- Pipes: pipes_{system_name}.json") 
        st.write(f"- PNG: p&id_{system_name}.png")
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
        st.write("🟢 **Green pipes**: Flow")
        st.write("🔵 **Blue pipes**: No flow") 
        st.write("🟣 **Purple pipes**: Selected")
        st.write("🟢 **Green valves**: Open")
        st.write("🔴 **Red valves**: Closed")

# ==================== MAIN DISPLAY ====================
if st.session_state.current_system == "home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    
    # Show system status
    st.markdown("---")
    st.subheader("📁 System Status")
    
    systems = ["mixing", "supply", "dgs", "return", "seal"]
    for system in systems:
        valves_path, pipes_path, png_path = find_system_files(system)
        
        status = "✅ READY" if all([valves_path, pipes_path, png_path]) else "❌ INCOMPLETE"
        st.write(f"**{system.title()}**: {status}")
        
        if valves_path:
            st.write(f"  - Valves: ✅ {os.path.basename(valves_path)}")
        else:
            st.write(f"  - Valves: ❌ Missing")
            
        if pipes_path:
            st.write(f"  - Pipes: ✅ {os.path.basename(pipes_path)}")
        else:
            st.write(f"  - Pipes: ❌ Missing")
            
        if png_path:
            st.write(f"  - P&ID: ✅ {os.path.basename(png_path)}")
        else:
            st.write(f"  - P&ID: ❌ Missing")

else:
    run_simulation(st.session_state.current_system)

st.markdown("---")
st.success("🎯 **Click systems above to view P&IDs and interact with valves!**")
