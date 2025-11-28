# streamlit_app.py - UPDATED FOR CORRECT PIPE-VALVE CORRELATIONS
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
if 'temp_valve_x' not in st.session_state:
    st.session_state.temp_valve_x = 0
if 'temp_valve_y' not in st.session_state:
    st.session_state.temp_valve_y = 0
if 'temp_pipe_x1' not in st.session_state:
    st.session_state.temp_pipe_x1 = 0
if 'temp_pipe_y1' not in st.session_state:
    st.session_state.temp_pipe_y1 = 0
if 'temp_pipe_x2' not in st.session_state:
    st.session_state.temp_pipe_x2 = 0
if 'temp_pipe_y2' not in st.session_state:
    st.session_state.temp_pipe_y2 = 0
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# ==================== PRESSURE SYSTEM CONFIGURATION ====================
def get_pressure_config(system_name):
    """Define pressure sources for each system"""
    pressure_config = {
        "mixing": {
            "pressure_sources": [1, 5],  # Pipe numbers that are pressure sources
            "special_valves": ["v-101", "v-102"]  # Valves that control pressure flow
        },
        "supply": {
            "pressure_sources": [1, 3, 7],
            "special_valves": ["v-201", "v-202"]
        },
        "dgs": {
            "pressure_sources": [1, 6, 11],
            "special_valves": ["v-301", "v-302"]
        },
        "return": {
            "pressure_sources": [2, 8],
            "special_valves": ["v-401", "v-402"]
        },
        "seal": {
            "pressure_sources": [1, 4, 9],
            "special_valves": ["v-501", "v-502"]
        }
    }
    return pressure_config.get(system_name, {"pressure_sources": [], "special_valves": []})

# ==================== CORRECT PIPE FIELD NAMES FOR EACH SYSTEM ====================
def get_pipe_field_name(system_name):
    """Get the correct pipe connection field name for each system"""
    pipe_fields = {
        "mixing": "pipes_mixing.json",
        "supply": "pipes_pressure_in.json", 
        "dgs": "pipes_dgs.json",
        "return": "pipes_pressure_return.json",
        "seal": "pipes_separation_seal.json"
    }
    return pipe_fields.get(system_name, "connected_pipes")

# ==================== PRESSURE PROPAGATION LOGIC ====================
def build_pressure_network(pipes, valves, system_name):
    """Build a network graph of pipes and valves using correct pipe connection data"""
    network = {}
    pipe_field = get_pipe_field_name(system_name)
    
    # Add all pipes to network
    for pipe_idx in range(len(pipes)):
        network[f"pipe_{pipe_idx}"] = {
            "type": "pipe",
            "connected_valves": []  # Will be populated from valve data
        }
    
    # Add all valves to network and connect pipes
    for valve_tag, valve_data in valves.items():
        # Use the correct pipe connection field for this system
        connected_pipes = valve_data.get(pipe_field, [])
        network[valve_tag] = {
            "type": "valve", 
            "connected_pipes": connected_pipes,
            "is_open": st.session_state.valve_states.get(valve_tag, False),
            "is_special": valve_tag in get_pressure_config(system_name)["special_valves"]
        }
        
        # Connect pipes back to this valve
        for pipe_idx in connected_pipes:
            pipe_id = f"pipe_{pipe_idx}"
            if pipe_id in network:
                network[pipe_id]["connected_valves"].append(valve_tag)
    
    return network

def propagate_pressure(network, pressure_sources, system_name):
    """Propagate pressure through the network based on valve states"""
    pressurized_nodes = set()
    config = get_pressure_config(system_name)
    
    # Start from pressure sources (convert to 0-based indices)
    for source_pipe in pressure_sources:
        pipe_id = f"pipe_{source_pipe-1}"
        pressurized_nodes.add(pipe_id)
    
    # Propagate pressure through the network
    changed = True
    while changed:
        changed = False
        
        for node_id, node_data in network.items():
            if node_id in pressurized_nodes:
                # This node has pressure, propagate to neighbors
                if node_data["type"] == "pipe":
                    # Pipe can propagate to connected valves
                    for valve_tag in node_data.get("connected_valves", []):
                        if valve_tag not in pressurized_nodes:
                            valve_data = network[valve_tag]
                            # Special valves must be open to allow flow
                            if valve_data["is_special"]:
                                if valve_data["is_open"]:  # Special valve is open
                                    pressurized_nodes.add(valve_tag)
                                    changed = True
                            else:
                                # Regular valves always allow flow
                                pressurized_nodes.add(valve_tag)
                                changed = True
                
                elif node_data["type"] == "valve":
                    # Valve can propagate to connected pipes if open
                    if node_data["is_open"]:  # Valve is open
                        for pipe_idx in node_data.get("connected_pipes", []):
                            pipe_id = f"pipe_{pipe_idx}"
                            if pipe_id not in pressurized_nodes:
                                pressurized_nodes.add(pipe_id)
                                changed = True
    
    return pressurized_nodes

def get_pipe_pressure_status(pipe_index, pressurized_nodes):
    """Check if a pipe has pressure and flow"""
    pipe_id = f"pipe_{pipe_index}"
    has_pressure = pipe_id in pressurized_nodes
    
    # For now, if pipe has pressure, it has flow
    # You can add more complex flow logic here later
    has_flow = has_pressure
    
    return has_pressure, has_flow

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
        st.session_state.edit_mode = False
        st.rerun()

with col2:
    if st.button("⚡ Supply", use_container_width=True):
        st.session_state.current_system = "supply"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.session_state.edit_mode = False
        st.rerun()

with col3:
    if st.button("🎮 DGS", use_container_width=True):
        st.session_state.current_system = "dgs"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.session_state.edit_mode = False
        st.rerun()

with col4:
    if st.button("🔄 Return", use_container_width=True):
        st.session_state.current_system = "return"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.session_state.edit_mode = False
        st.rerun()

with col5:
    if st.button("🔒 Seal", use_container_width=True):
        st.session_state.current_system = "seal"
        st.session_state.selected_pipe = None
        st.session_state.selected_valve = None
        st.session_state.calibration_mode = False
        st.session_state.edit_mode = False
        st.rerun()

st.markdown("---")

# ==================== RENDERING ====================
def render_pid_with_overlay(valves, pipes, png_path, system_name, pressurized_nodes):
    """Render P&ID with interactive overlays and pressure visualization"""
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
    
    # Draw pipes with pressure coloring
    for i, pipe in enumerate(pipes):
        has_pressure, has_flow = get_pipe_pressure_status(i, pressurized_nodes)
        
        if i == st.session_state.selected_pipe:
            color = (180, 0, 255)  # Purple for selected pipe
            width = 8
        elif has_flow:
            color = (0, 255, 0)  # Green for flowing pipe
            width = 6
        elif has_pressure:
            color = (100, 180, 255)  # Light blue for pressurized but no flow
            width = 5
        else:
            color = (100, 100, 255)  # Dark blue for no pressure
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
            outline_width = 2
            radius = 4
        elif is_open:
            color = (0, 255, 0)  # Green for open
            outline = "white"
            outline_width = 2
            radius = 4
        else:
            color = (255, 0, 0)  # Red for closed
            outline = "white"
            outline_width = 2
            radius = 4
        
        x, y = valve_data["x"], valve_data["y"]
        # Draw valve circle
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                    fill=color, outline=outline, width=outline_width)
        # Text offset
        draw.text((x+7, y-9), tag, fill="white", stroke_fill="black", stroke_width=1)
    
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
    
    # Build pressure network and propagate pressure
    config = get_pressure_config(system_name)
    network = build_pressure_network(pipes, valves, system_name)
    pressurized_nodes = propagate_pressure(network, config["pressure_sources"], system_name)
    
    # Count pressurized pipes
    pressurized_pipes = sum(1 for i in range(len(pipes)) 
                          if get_pipe_pressure_status(i, pressurized_nodes)[0])
    flowing_pipes = sum(1 for i in range(len(pipes)) 
                       if get_pipe_pressure_status(i, pressurized_nodes)[1])
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Valve Controls")
        for tag in valves:
            state = st.session_state.valve_states.get(tag, False)
            # Mark special valves
            special_indicator = " ⭐" if tag in config["special_valves"] else ""
            label = f"{'🟢 OPEN' if state else '🔴 CLOSED'} {tag}{special_indicator}"
            if st.button(label, key=f"valve_{system_name}_{tag}"):
                st.session_state.valve_states[tag] = not state
                st.rerun()
        
        st.header("📏 Calibration Tools")
        
        # Calibration mode toggle
        if st.button("🎯 Toggle Calibration Mode", key="calib_toggle", use_container_width=True):
            st.session_state.calibration_mode = not st.session_state.calibration_mode
            st.rerun()
        
        if st.session_state.calibration_mode:
            st.warning("🔧 CALIBRATION MODE ACTIVE")
            
            # Edit mode toggle
            if st.button("✏️ Toggle Edit Mode", key="edit_toggle", use_container_width=True):
                st.session_state.edit_mode = not st.session_state.edit_mode
                st.rerun()
            
            if st.session_state.edit_mode:
                st.error("🗑️ EDIT MODE - Can delete/rename items")
                
                # Valve management
                st.subheader("🔧 Valve Management")
                
                # Add new valve
                st.write("**Add New Valve:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_valve_id = st.text_input("Valve ID", "v-New", key="new_valve_id")
                with col2:
                    new_valve_x = st.number_input("X", value=400, key="new_valve_x")
                with col3:
                    new_valve_y = st.number_input("Y", value=300, key="new_valve_y")
                
                if st.button("➕ Add Valve", key="add_valve"):
                    if new_valve_id and new_valve_id not in valves:
                        pipe_field = get_pipe_field_name(system_name)
                        valves[new_valve_id] = {
                            "x": new_valve_x, 
                            "y": new_valve_y,
                            pipe_field: []  # Use correct pipe field name
                        }
                        st.session_state.valve_states[new_valve_id] = False
                        save_system_data(system_name, valves, pipes)
                        st.success(f"✅ Added valve {new_valve_id}")
                        st.rerun()
                    else:
                        st.error("❌ Valve ID already exists or is empty")
                
                # Rename selected valve
                if st.session_state.selected_valve:
                    st.write("**Rename Selected Valve:**")
                    new_name = st.text_input("New Name", st.session_state.selected_valve, key="rename_valve")
                    if st.button("🔄 Rename Valve", key="rename_valve_btn"):
                        if new_name and new_name not in valves:
                            valves[new_name] = valves.pop(st.session_state.selected_valve)
                            st.session_state.valve_states[new_name] = st.session_state.valve_states.pop(st.session_state.selected_valve, False)
                            st.session_state.selected_valve = new_name
                            save_system_data(system_name, valves, pipes)
                            st.success(f"✅ Renamed to {new_name}")
                            st.rerun()
                        else:
                            st.error("❌ Name already exists or is empty")
                
                # Delete selected valve
                if st.session_state.selected_valve:
                    if st.button("🗑️ Delete Selected Valve", key="delete_valve"):
                        del valves[st.session_state.selected_valve]
                        if st.session_state.selected_valve in st.session_state.valve_states:
                            del st.session_state.valve_states[st.session_state.selected_valve]
                        st.session_state.selected_valve = None
                        save_system_data(system_name, valves, pipes)
                        st.success("✅ Valve deleted")
                        st.rerun()
                
                # Pipe management
                st.subheader("🔧 Pipe Management")
                
                # Add new pipe
                st.write("**Add New Pipe:**")
                col1, col2 = st.columns(2)
                with col1:
                    new_pipe_x1 = st.number_input("Start X", value=350, key="new_pipe_x1")
                    new_pipe_y1 = st.number_input("Start Y", value=250, key="new_pipe_y1")
                with col2:
                    new_pipe_x2 = st.number_input("End X", value=450, key="new_pipe_x2")
                    new_pipe_y2 = st.number_input("End Y", value=250, key="new_pipe_y2")
                
                if st.button("➕ Add Pipe", key="add_pipe"):
                    pipes.append({
                        "x1": new_pipe_x1,
                        "y1": new_pipe_y1,
                        "x2": new_pipe_x2,
                        "y2": new_pipe_y2
                    })
                    save_system_data(system_name, valves, pipes)
                    st.success("✅ Added new pipe")
                    st.rerun()
                
                # Delete selected pipe
                if st.session_state.selected_pipe is not None:
                    if st.button("🗑️ Delete Selected Pipe", key="delete_pipe"):
                        pipes.pop(st.session_state.selected_pipe)
                        st.session_state.selected_pipe = None
                        save_system_data(system_name, valves, pipes)
                        st.success("✅ Pipe deleted")
                        st.rerun()
            
            # Valve selection for calibration
            st.subheader("Select Valve to Calibrate")
            valve_list = list(valves.keys())
            if not valve_list:
                st.error("No valves found in data")
            else:
                selected_valve = st.selectbox("Choose valve:", valve_list, 
                                             key="valve_select")
                
                if st.button("🎯 Select This Valve", key="select_valve_btn"):
                    st.session_state.selected_valve = selected_valve
                    st.session_state.selected_pipe = None
                    # Store current position in temp state
                    if selected_valve in valves:
                        st.session_state.temp_valve_x = valves[selected_valve]["x"]
                        st.session_state.temp_valve_y = valves[selected_valve]["y"]
                    st.rerun()
            
            if st.session_state.selected_valve and st.session_state.selected_valve in valves:
                current_valve = valves[st.session_state.selected_valve]
                st.info(f"**Selected: {st.session_state.selected_valve}**")
                
                # Show current location
                st.subheader("📍 Current Location")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("X Position", current_valve["x"])
                with col2:
                    st.metric("Y Position", current_valve["y"])
                
                # Show connected pipes
                pipe_field = get_pipe_field_name(system_name)
                connected_pipes = current_valve.get(pipe_field, [])
                st.write(f"**Connected Pipes:** {[f'Pipe {p+1}' for p in connected_pipes]}")
                
                # Move valve to center
                if st.button("🎯 Move to Center", key="center_valve"):
                    try:
                        img = Image.open(png_path)
                        width, height = img.size
                        valves[st.session_state.selected_valve]["x"] = width // 2
                        valves[st.session_state.selected_valve]["y"] = height // 2
                        st.session_state.temp_valve_x = width // 2
                        st.session_state.temp_valve_y = height // 2
                        save_system_data(system_name, valves, pipes)
                        st.success("✅ Valve moved to center!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                # Manual position adjustment
                st.subheader("✏️ Adjust Position")
                col1, col2 = st.columns(2)
                with col1:
                    new_x = st.number_input("X Position", 
                                           value=st.session_state.temp_valve_x,
                                           key="valve_x_input")
                with col2:
                    new_y = st.number_input("Y Position",
                                           value=st.session_state.temp_valve_y,
                                           key="valve_y_input")
                
                if st.button("💾 Update Valve Position", key="update_valve"):
                    valves[st.session_state.selected_valve]["x"] = new_x
                    valves[st.session_state.selected_valve]["y"] = new_y
                    save_system_data(system_name, valves, pipes)
                    st.success("✅ Valve position updated!")
                    st.rerun()
            
            # Pipe selection for calibration
            st.subheader("Select Pipe to Calibrate")
            if pipes:
                pipe_options = [f"Pipe {i+1}" for i in range(len(pipes))]
                selected_pipe_name = st.selectbox("Choose pipe:", pipe_options,
                                                key="pipe_select")
                
                if st.button("🎯 Select This Pipe", key="select_pipe_btn"):
                    pipe_idx = pipe_options.index(selected_pipe_name)
                    st.session_state.selected_pipe = pipe_idx
                    st.session_state.selected_valve = None
                    # Store current position in temp state
                    if pipe_idx < len(pipes):
                        pipe = pipes[pipe_idx]
                        st.session_state.temp_pipe_x1 = pipe["x1"]
                        st.session_state.temp_pipe_y1 = pipe["y1"]
                        st.session_state.temp_pipe_x2 = pipe["x2"]
                        st.session_state.temp_pipe_y2 = pipe["y2"]
                    st.rerun()
            else:
                st.error("No pipes found in data")
            
            if st.session_state.selected_pipe is not None and st.session_state.selected_pipe < len(pipes):
                current_pipe = pipes[st.session_state.selected_pipe]
                st.info(f"**Selected: Pipe {st.session_state.selected_pipe + 1}**")
                
                # Show current pipe locations
                st.subheader("📍 Current Locations")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Start X", current_pipe["x1"])
                    st.metric("Start Y", current_pipe["y1"])
                with col2:
                    st.metric("End X", current_pipe["x2"])
                    st.metric("End Y", current_pipe["y2"])
                
                # Move pipe to center
                if st.button("🎯 Move Pipe to Center", key="center_pipe"):
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
                        st.success("✅ Pipe moved to center!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                # Manual pipe position adjustment
                st.subheader("✏️ Adjust Positions")
                col1, col2 = st.columns(2)
                with col1:
                    x1 = st.number_input("Start X", value=st.session_state.temp_pipe_x1, key="pipe_x1_input")
                    y1 = st.number_input("Start Y", value=st.session_state.temp_pipe_y1, key="pipe_y1_input")
                with col2:
                    x2 = st.number_input("End X", value=st.session_state.temp_pipe_x2, key="pipe_x2_input")
                    y2 = st.number_input("End Y", value=st.session_state.temp_pipe_y2, key="pipe_y2_input")
                
                if st.button("💾 Update Pipe Position", key="update_pipe"):
                    pipes[st.session_state.selected_pipe] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                    save_system_data(system_name, valves, pipes)
                    st.success("✅ Pipe position updated!")
                    st.rerun()
            
            # Deselect button
            if st.button("❌ Deselect All", key="deselect_all"):
                st.session_state.selected_valve = None
                st.session_state.selected_pipe = None
                st.rerun()
        
        else:
            st.info("🔧 Enable calibration to adjust positions")
        
        st.header("📊 Pressure Status")
        open_valves = sum(st.session_state.valve_states.values())
        st.metric("Open Valves", open_valves)
        st.metric("Pressurized Pipes", pressurized_pipes)
        st.metric("Flowing Pipes", flowing_pipes)
        st.metric("Total Pipes", len(pipes))
        
        # Clear all valves button
        if st.button("🔄 Clear All Valves", key="clear_valves"):
            for tag in valves:
                st.session_state.valve_states[tag] = False
            st.rerun()
    
    # Main display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        image = render_pid_with_overlay(valves, pipes, png_path, system_name, pressurized_nodes)
        st.image(image, use_container_width=True, 
                caption=f"{display_names[system_name]} - Green=Flow | Light Blue=Pressurized | Dark Blue=No Pressure | Purple=Selected")
    
    with col2:
        st.header("🎯 Legend")
        st.write("🟢 **Green pipes**: Fluid flowing")
        st.write("🔵 **Light blue pipes**: Pressurized but no flow")
        st.write("🔵 **Dark blue pipes**: No pressure")
        st.write("🟣 **Purple**: Selected for calibration")
        st.write("🟢 **Green valves**: Open")
        st.write("🔴 **Red valves**: Closed")
        st.write("⭐ **Special valves**: Control pressure flow")
        if st.session_state.edit_mode:
            st.write("🗑️ **Edit Mode**: Can add/delete/rename")
        st.write("---")
        st.info("💡 **Toggle valves** to control pressure flow")
        st.info("💡 **Special valves** (⭐) must be open for flow")
        st.info("💡 **Enable Calibration** to adjust positions")

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
st.success("🎯 **Interactive P&ID Simulation** - Now with system-specific pipe correlations! 🎯")
