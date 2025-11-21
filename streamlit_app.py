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
if 'selected_valve' not in st.session_state:
    st.session_state.selected_valve = None
if 'calibration_mode' not in st.session_state:
    st.session_state.calibration_mode = False

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
            "valves": "data/valves_separatoin_seal.json",
            "pipes": "data/pipes_separation_seal.json",
            "png": "assets/p&id_separation_seal.png"
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
        except Exception as e:
            st.error(f"❌ Error loading pipes: {e}")
    else:
        st.error(f"❌ Missing: {pipes_path}")
    
    # Check PNG
    if not png_path or not os.path.exists(png_path):
        st.error(f"❌ Missing: {png_path}")
        png_path = None
    
    return valves, pipes, png_path

def save_system_data(system_name, valves, pipes):
    """Save data back to files"""
    valves_path, pipes_path, _ = get_system_files(system_name)
    
    if valves_path:
        try:
            with open(valves_path, 'w') as f:
                json.dump(valves, f, indent=2)
            st.sidebar.success(f"💾 Saved valves to {os.path.basename(valves_path)}")
        except Exception as e:
            st.error(f"❌ Error saving valves: {e}")
    
    if pipes_path:
        try:
            with open(pipes_path, 'w') as f:
                json.dump(pipes, f, indent=2)
            st.sidebar.success(f"💾 Saved pipes to {os.path.basename(pipes_path)}")
        except Exception as e:
            st.error(f"❌ Error saving pipes: {e}")

# ==================== NAVIGATION ====================
st.title("🏭 Rig Multi-P&ID Simulation")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔧 Mixing", use_container_width=True):
        st.session_state.current_system = "mixing"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.rerun()

with col2:
    if st.button("⚡ Supply", use_container_width=True):
        st.session_state.current_system = "supply"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.rerun()

with col3:
    if st.button("🎮 DGS", use_container_width=True):
        st.session_state.current_system = "dgs"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.rerun()

with col4:
    if st.button("🔄 Return", use_container_width=True):
        st.session_state.current_system = "return"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.rerun()

with col5:
    if st.button("🔒 Seal", use_container_width=True):
        st.session_state.current_system = "seal"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
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
        
        if i == st.session_state.selected_pipe:
            color = (180, 0, 255)  # Purple for selected pipe
            width = 8
        elif has_flow:
            color = (0, 255, 0)  # Green for flow
            width = 6
        else:
            color = (100, 100, 255)  # Blue for no flow
            width = 4
            
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
        
        # Draw pipe endpoints if selected
        if i == st.session_state.selected_pipe:
            draw.ellipse([pipe["x1"]-6, pipe["y1"]-6, pipe["x1"]+6, pipe["y1"]+6], 
                        fill=(255, 0, 0), outline="white", width=2)
            draw.ellipse([pipe["x2"]-6, pipe["y2"]-6, pipe["x2"]+6, pipe["y2"]+6], 
                        fill=(255, 0, 0), outline="white", width=2)
    
    # Draw valves
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        
        if tag == st.session_state.selected_valve:
            color = (180, 0, 255)  # Purple for selected valve
            outline = "white"
            outline_width = 3
        elif is_open:
            color = (0, 255, 0)  # Green for open
            outline = "white"
            outline_width = 2
        else:
            color = (255, 0, 0)  # Red for closed
            outline = "white"
            outline_width = 2
        
        x, y = valve_data["x"], valve_data["y"]
        draw.ellipse([x-12, y-12, x+12, y+12], fill=color, outline=outline, width=outline_width)
        draw.text((x+15, y-15), tag, fill="white", stroke_fill="black", stroke_width=1)
    
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
        return
    
    if not png_path:
        st.error(f"❌ P&ID image not found")
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
        
        st.header("📏 Calibration Tools")
        
        # Calibration mode toggle
        calibration_on = st.session_state.calibration_mode
        if st.button("🎯 Toggle Calibration Mode", use_container_width=True):
            st.session_state.calibration_mode = not st.session_state.calibration_mode
            st.rerun()
        
        if st.session_state.calibration_mode:
            st.warning("🔧 CALIBRATION MODE ACTIVE")
            
            # Valve selection for calibration
            st.subheader("Select Valve to Calibrate")
            valve_list = list(valves.keys())
            selected_valve = st.selectbox("Choose valve:", valve_list, 
                                         index=valve_list.index(st.session_state.selected_valve) 
                                         if st.session_state.selected_valve in valve_list else 0,
                                         key="valve_select")
            
            if selected_valve != st.session_state.selected_valve:
                st.session_state.selected_valve = selected_valve
                st.session_state.selected_pipe = None
                st.rerun()
            
            if st.session_state.selected_valve:
                st.info(f"Selected: {st.session_state.selected_valve}")
                
                # Move valve to center
                if st.button("🎯 Move to Center", use_container_width=True):
                    try:
                        img = Image.open(png_path)
                        width, height = img.size
                        valves[st.session_state.selected_valve]["x"] = width // 2
                        valves[st.session_state.selected_valve]["y"] = height // 2
                        save_system_data(system_name, valves, pipes)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                # Manual position adjustment
                col1, col2 = st.columns(2)
                with col1:
                    new_x = st.number_input("X Position", 
                                           value=valves[st.session_state.selected_valve]["x"],
                                           key="valve_x")
                with col2:
                    new_y = st.number_input("Y Position",
                                           value=valves[st.session_state.selected_valve]["y"],
                                           key="valve_y")
                
                if st.button("💾 Update Valve Position", use_container_width=True):
                    valves[st.session_state.selected_valve]["x"] = new_x
                    valves[st.session_state.selected_valve]["y"] = new_y
                    save_system_data(system_name, valves, pipes)
                    st.rerun()
            
            # Pipe selection for calibration
            st.subheader("Select Pipe to Calibrate")
            pipe_options = [f"Pipe {i+1}" for i in range(len(pipes))]
            selected_pipe_idx = st.selectbox("Choose pipe:", pipe_options,
                                            index=st.session_state.selected_pipe if st.session_state.selected_pipe is not None else 0,
                                            key="pipe_select")
            
            if selected_pipe_idx:
                pipe_idx = pipe_options.index(selected_pipe_idx)
                if pipe_idx != st.session_state.selected_pipe:
                    st.session_state.selected_pipe = pipe_idx
                    st.session_state.selected_valve = None
                    st.rerun()
            
            if st.session_state.selected_pipe is not None:
                st.info(f"Selected: Pipe {st.session_state.selected_pipe + 1}")
                pipe = pipes[st.session_state.selected_pipe]
                
                # Move pipe to center
                if st.button("🎯 Move Pipe to Center", use_container_width=True):
                    try:
                        img = Image.open(png_path)
                        width, height = img.size
                        center_x, center_y = width // 2, height // 2
                        length = 100  # Default pipe length
                        
                        pipes[st.session_state.selected_pipe] = {
                            "x1": center_x - length // 2,
                            "y1": center_y,
                            "x2": center_x + length // 2,
                            "y2": center_y
                        }
                        save_system_data(system_name, valves, pipes)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                # Manual pipe position adjustment
                col1, col2 = st.columns(2)
                with col1:
                    x1 = st.number_input("Start X", value=pipe["x1"], key="pipe_x1")
                    y1 = st.number_input("Start Y", value=pipe["y1"], key="pipe_y1")
                with col2:
                    x2 = st.number_input("End X", value=pipe["x2"], key="pipe_x2")
                    y2 = st.number_input("End Y", value=pipe["y2"], key="pipe_y2")
                
                if st.button("💾 Update Pipe Position", use_container_width=True):
                    pipes[st.session_state.selected_pipe] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                    save_system_data(system_name, valves, pipes)
                    st.rerun()
            
            # Deselect button
            if st.button("❌ Deselect All", use_container_width=True):
                st.session_state.selected_valve = None
                st.session_state.selected_pipe = None
                st.rerun()
        
        else:
            st.info("🔧 Enable calibration to adjust positions")
        
        st.header("📊 Status")
        open_valves = sum(st.session_state.valve_states.values())
        st.metric("Open Valves", open_valves)
        st.metric("Total Valves", len(valves))
        st.metric("Total Pipes", len(pipes))
        
        # Clear all valves button
        if st.button("🔄 Clear All Valves", use_container_width=True):
            for tag in valves:
                st.session_state.valve_states[tag] = False
            st.rerun()
    
    # Main display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        image = render_pid_with_overlay(valves, pipes, png_path, display_names[system_name])
        st.image(image, use_container_width=True, 
                caption=f"{display_names[system_name]} - Purple=Selected | Green=Flow | Red=Closed")
    
    with col2:
        st.header("🎯 Legend")
        st.write("🟣 **Purple**: Selected for calibration")
        st.write("🟢 **Green pipes/valves**: Flow/Open")
        st.write("🔵 **Blue pipes**: No flow")
        st.write("🔴 **Red valves**: Closed")
        st.write("---")
        st.info("💡 **Enable Calibration** to adjust positions")
        st.info("💡 **Select items** to make them purple")
        st.info("💡 **Move to Center** for easy positioning")

# ==================== MAIN DISPLAY ====================
if st.session_state.current_system == "home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    st.markdown("👆 **Select a system from the buttons above to view P&ID diagrams and control valves**")
    
    # File status
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
st.success("🎯 **Interactive P&ID Simulation** - Now with position calibration! 🎯")
