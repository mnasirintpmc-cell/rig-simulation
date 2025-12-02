# streamlit_app.py - UPDATED FOR DYNAMIC VALVE TOGGLE
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

# ----------------- SESSION STATE -----------------
session_defaults = {
    "current_system": "home",
    "valve_states": {},
    "selected_pipe": None,
    "selected_valve": None,
    "calibration_mode": False,
    "edit_mode": False,
    "temp_valve_x": 0,
    "temp_valve_y": 0,
    "temp_pipe_x1": 0,
    "temp_pipe_y1": 0,
    "temp_pipe_x2": 0,
    "temp_pipe_y2": 0
}

for key, val in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------- CONFIGURATION -----------------
def get_pressure_config(system_name):
    """Define pressure sources and special valves for each system."""
    configs = {
        "mixing": {"pressure_sources": [1, 5], "special_valves": ["v-101", "v-102"]},
        "supply": {"pressure_sources": [1, 3, 7], "special_valves": ["v-201", "v-202"]},
        "dgs": {"pressure_sources": [1, 6, 11], "special_valves": ["v-301", "v-302"]},
        "return": {"pressure_sources": [2, 8], "special_valves": ["v-401", "v-402"]},
        "seal": {"pressure_sources": [1, 4, 9], "special_valves": ["v-501", "v-502"]}
    }
    return configs.get(system_name, {"pressure_sources": [], "special_valves": []})

def get_pipe_field_name(system_name):
    """Return the pipe field name for a system."""
    pipe_fields = {
        "mixing": "pipes_mixing.json",
        "supply": "pipes_pressure_in.json",
        "dgs": "pipes_dgs.json",
        "return": "pipes_pressure_return.json",
        "seal": "pipes_separation_seal.json"
    }
    return pipe_fields.get(system_name, "connected_pipes")

def get_system_files(system_name):
    """Get valves/pipes/PNG file paths."""
    file_map = {
        "mixing": {"valves":"data/valves_mixing.json","pipes":"data/pipes_mixing.json","png":"assets/p&id_mixing.png"},
        "supply": {"valves":"data/valves_pressure_in.json","pipes":"data/pipes_pressure_in.json","png":"assets/p&id_pressure_in.png"},
        "dgs": {"valves":"data/valves_dgs.json","pipes":"data/pipes_dgs.json","png":"assets/p&id_dgs.png"},
        "return": {"valves":"data/valves_pressure_return.json","pipes":"data/pipes_pressure_return.json","png":"assets/p&id_pressure_return.png"},
        "seal": {"valves":"data/valves_separatoin_seal.json","pipes":"data/pipes_separation_seal.json","png":"assets/p&id_separation_seal.png"}
    }
    return file_map.get(system_name, {"valves":None,"pipes":None,"png":None}).values()

def load_system_data(system_name):
    valves_path, pipes_path, png_path = get_system_files(system_name)
    valves, pipes = {}, []
    if valves_path and os.path.exists(valves_path):
        with open(valves_path, 'r') as f: valves = json.load(f)
    if pipes_path and os.path.exists(pipes_path):
        with open(pipes_path, 'r') as f: pipes = json.load(f)
    if not png_path or not os.path.exists(png_path): png_path = None
    return valves, pipes, png_path

def save_system_data(system_name, valves, pipes):
    valves_path, pipes_path, _ = get_system_files(system_name)
    if valves_path:
        with open(valves_path, 'w') as f: json.dump(valves, f, indent=2)
    if pipes_path:
        with open(pipes_path, 'w') as f: json.dump(pipes, f, indent=2)

# ----------------- PRESSURE NETWORK -----------------
def build_pressure_network(pipes, valves, system_name):
    network = {}
    pipe_field = get_pipe_field_name(system_name)
    for i in range(len(pipes)):
        network[f"pipe_{i}"] = {"type":"pipe", "connected_valves":[]}
    for tag, valve_data in valves.items():
        connected_pipes = valve_data.get(pipe_field, [])
        network[tag] = {
            "type": "valve",
            "connected_pipes": connected_pipes,
            "is_open": st.session_state.valve_states.get(tag, False),
            "is_special": tag in get_pressure_config(system_name)["special_valves"]
        }
        for p in connected_pipes:
            pipe_id = f"pipe_{p}"
            if pipe_id in network:
                network[pipe_id]["connected_valves"].append(tag)
    return network

def propagate_pressure(network, pressure_sources, system_name):
    pressurized_nodes = set()
    for source in pressure_sources:
        pressurized_nodes.add(f"pipe_{source-1}")
    changed = True
    while changed:
        changed = False
        for node_id, node_data in network.items():
            if node_id in pressurized_nodes:
                if node_data["type"]=="pipe":
                    for valve_tag in node_data.get("connected_valves", []):
                        if valve_tag not in pressurized_nodes:
                            valve_data = network[valve_tag]
                            if valve_data["is_special"]:
                                if valve_data["is_open"]:
                                    pressurized_nodes.add(valve_tag); changed=True
                            else:
                                pressurized_nodes.add(valve_tag); changed=True
                elif node_data["type"]=="valve":
                    if node_data["is_open"]:
                        for p_idx in node_data.get("connected_pipes", []):
                            pipe_id = f"pipe_{p_idx}"
                            if pipe_id not in pressurized_nodes:
                                pressurized_nodes.add(pipe_id); changed=True
    return pressurized_nodes

def get_pipe_pressure_status(pipe_index, pressurized_nodes):
    pipe_id = f"pipe_{pipe_index}"
    has_pressure = pipe_id in pressurized_nodes
    has_flow = has_pressure
    return has_pressure, has_flow

# ----------------- RENDERING -----------------
def render_pid_with_overlay(valves, pipes, png_path, system_name, pressurized_nodes):
    try: img = Image.open(png_path).convert("RGBA")
    except: img = Image.new('RGBA', (800,600),(40,40,60))
    draw = ImageDraw.Draw(img)
    
    for i, pipe in enumerate(pipes):
        has_pressure, has_flow = get_pipe_pressure_status(i, pressurized_nodes)
        if i==st.session_state.selected_pipe: color,width=(180,0,255),8
        elif has_flow: color,width=(0,255,0),6
        elif has_pressure: color,width=(100,180,255),5
        else: color,width=(100,100,255),4
        draw.line([(pipe["x1"],pipe["y1"]),(pipe["x2"],pipe["y2"])],fill=color,width=width)
    
    for tag, valve_data in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        if tag==st.session_state.selected_valve: color,outline,radius=(180,0,255),"white",4
        elif is_open: color,outline,radius=(0,255,0),"white",4
        else: color,outline,radius=(255,0,0),"white",4
        x,y = valve_data["x"],valve_data["y"]
        draw.ellipse([x-radius,y-radius,x+radius,y+radius],fill=color,outline=outline,width=2)
        draw.text((x+7,y-9),tag,fill="white")
    return img.convert("RGB")

# ----------------- SIMULATION -----------------
def run_simulation(system_name):
    display_names = {"mixing":"Mixing Area","supply":"Pressure Supply","dgs":"DGS Simulation","return":"Pressure Return","seal":"Separation Seal"}
    st.header(f"{display_names[system_name]} Simulation")
    
    valves, pipes, png_path = load_system_data(system_name)
    if not valves or not pipes: st.error("❌ Missing JSON data"); return
    if not png_path: st.error("❌ P&ID image not found"); return
    for tag in valves:
        if tag not in st.session_state.valve_states: st.session_state.valve_states[tag]=False
    
    config = get_pressure_config(system_name)
    network = build_pressure_network(pipes, valves, system_name)
    pressurized_nodes = propagate_pressure(network, config["pressure_sources"], system_name)
    
    # ----------- SIDEBAR VALVE CONTROLS -----------
    with st.sidebar:
        st.header("🎛️ Valve Controls")
        for tag in valves:
            special = " ⭐" if tag in config["special_valves"] else ""
            st.session_state.valve_states[tag] = st.checkbox(f"{tag}{special}", value=st.session_state.valve_states[tag], key=f"valve_{system_name}_{tag}")
        
        # Calibration / Edit Section remains intact
        st.header("📏 Calibration Tools")
        if st.button("🎯 Toggle Calibration Mode"): st.session_state.calibration_mode=not st.session_state.calibration_mode; st.rerun()
    
    # ----------- MAIN DISPLAY -----------
    col1, col2 = st.columns([3,1])
    with col1:
        image = render_pid_with_overlay(valves,pipes,png_path,system_name,pressurized_nodes)
        st.image(image,use_container_width=True,caption=f"{display_names[system_name]} Simulation")
    with col2:
        st.header("🎯 Legend")
        st.write("🟢 Flowing pipes | 🔵 Pressurized | 🔵 No pressure | 🟣 Selected | Green valves=open | Red valves=closed | ⭐ Special valves")

# ----------------- NAVIGATION -----------------
st.title("🏭 Rig Multi-P&ID Simulation")
col1, col2, col3, col4, col5 = st.columns(5)
systems = [("mixing","🔧 Mixing"),("supply","⚡ Supply"),("dgs","🎮 DGS"),("return","🔄 Return"),("seal","🔒 Seal")]
for i,(sys_name,label) in enumerate(systems):
    with [col1,col2,col3,col4,col5][i]:
        if st.button(label,use_container_width=True):
            st.session_state.current_system=sys_name
            st.session_state.selected_pipe=None
            st.session_state.selected_valve=None
            st.session_state.calibration_mode=False
            st.session_state.edit_mode=False
            st.rerun()

# ----------------- MAIN -----------------
if st.session_state.current_system=="home":
    st.markdown("## 🏠 Welcome to Rig Simulation")
    st.markdown("👆 Select a system above to simulate")
else:
    run_simulation(st.session_state.current_system)
