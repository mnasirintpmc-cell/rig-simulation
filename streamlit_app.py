import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(page_title="Rig Simulation Dashboard", page_icon="🏭", layout="wide")

# ================== SESSION STATE ==================
for key in ['current_system', 'valve_states', 'selected_pipe', 'selected_valve',
            'calibration_mode', 'edit_mode']:
    if key not in st.session_state:
        st.session_state[key] = False if 'mode' in key else None

if st.session_state.current_system is None:
    st.session_state.current_system = "home"

# ================== SYSTEM CONFIG ==================
def get_pressure_config(system_name):
    config = {
        "mixing": {"pressure_sources": [1,5], "special_valves": ["v-101","v-102"]},
        "supply": {"pressure_sources": [1,3,7], "special_valves": ["v-201","v-202"]},
        "dgs": {"pressure_sources": [1,6,11], "special_valves": ["v-301","v-302"]},
        "return": {"pressure_sources": [2,8], "special_valves": ["v-401","v-402"]},
        "seal": {"pressure_sources": [1,4,9], "special_valves": ["v-501","v-502"]}
    }
    return config.get(system_name, {"pressure_sources": [], "special_valves": []})

def get_system_files(system_name):
    files = {
        "mixing": {"valves":"data/valves_mixing.json","pipes":"data/pipes_mixing.json","png":"assets/p&id_mixing.png"},
        "supply": {"valves":"data/valves_pressure_in.json","pipes":"data/pipes_pressure_in.json","png":"assets/p&id_pressure_in.png"},
        "dgs": {"valves":"data/valves_dgs.json","pipes":"data/pipes_dgs.json","png":"assets/p&id_dgs.png"},
        "return": {"valves":"data/valves_pressure_return.json","pipes":"data/pipes_pressure_return.json","png":"assets/p&id_pressure_return.png"},
        "seal": {"valves":"data/valves_separatoin_seal.json","pipes":"data/pipes_separation_seal.json","png":"assets/p&id_separation_seal.png"}
    }
    return files.get(system_name, {"valves":None,"pipes":None,"png":None})

def load_system_data(system_name):
    files = get_system_files(system_name)
    valves, pipes, png_path = {}, [], None

    if files["valves"] and os.path.exists(files["valves"]):
        with open(files["valves"], "r") as f:
            valves = json.load(f)

    if files["pipes"] and os.path.exists(files["pipes"]):
        with open(files["pipes"], "r") as f:
            pipes = json.load(f)

    if files["png"] and os.path.exists(files["png"]):
        png_path = files["png"]

    return valves, pipes, png_path

# ================== NETWORK BUILD ==================
def build_network(valves, pipes, system_name):
    pipe_field = f"pipes_{system_name}.json"
    network = {}

    # Initialize pipes
    for i, pipe in enumerate(pipes):
        network[f"pipe_{i}"] = {"type":"pipe","connected_valves":[],"pressurized":False}

    # Initialize valves and connect pipes
    for vtag, vdata in valves.items():
        connected_pipes = vdata.get(pipe_field, [])
        network[vtag] = {
            "type":"valve",
            "connected_pipes":connected_pipes,
            "is_open": st.session_state.valve_states.get(vtag, vdata.get("state","closed").lower()=="open"),
            "is_special": vtag in get_pressure_config(system_name)["special_valves"]
        }
        for pi in connected_pipes:
            pid = f"pipe_{pi}"
            if pid in network:
                network[pid]["connected_valves"].append(vtag)

    return network

# ================== PRESSURE PROPAGATION ==================
def propagate_pressure(network, pressure_sources):
    pressurized = set()
    for src in pressure_sources:
        pid = f"pipe_{src-1}"  # 0-indexed
        pressurized.add(pid)

    changed = True
    while changed:
        changed = False
        for nid, node in network.items():
            if nid in pressurized:
                if node["type"]=="pipe":
                    for v in node["connected_valves"]:
                        vdata = network[v]
                        if v not in pressurized and (not vdata["is_special"] or vdata["is_open"]):
                            pressurized.add(v)
                            changed = True
                elif node["type"]=="valve" and node["is_open"]:
                    for pi in node["connected_pipes"]:
                        pid = f"pipe_{pi}"
                        if pid not in pressurized:
                            pressurized.add(pid)
                            changed = True
    return pressurized

def get_pipe_flow(pipe_idx, network):
    pid = f"pipe_{pipe_idx}"
    # Flow active if at least one connected valve is open
    for vtag in network[pid]["connected_valves"]:
        if network[vtag]["is_open"]:
            return True
    return False

# ================== RENDER ==================
def render_pid(valves, pipes, png_path, system_name, network):
    try:
        img = Image.open(png_path).convert("RGBA")
    except:
        img = Image.new("RGBA",(800,600),(40,40,60))
    draw = ImageDraw.Draw(img)

    # Draw pipes
    for i, pipe in enumerate(pipes):
        pid = f"pipe_{i}"
        flow_active = get_pipe_flow(i, network)
        color = (0,255,0) if flow_active else ((100,180,255) if network[pid]["pressurized"] else (100,100,255))
        width = 6 if flow_active else 5 if network[pid]["pressurized"] else 4
        draw.line([(pipe["x1"],pipe["y1"]),(pipe["x2"],pipe["y2"])],fill=color,width=width)

    # Draw valves
    for tag,vdata in valves.items():
        is_open = network[tag]["is_open"]
        x,y = vdata["x"],vdata["y"]
        radius = 4
        fill = (0,255,0) if is_open else (255,0,0)
        draw.ellipse([x-radius,y-radius,x+radius,y+radius],fill=fill)
        draw.text((x+7,y-9),tag,fill="white")
    return img.convert("RGB")

# ================== RUN SYSTEM ==================
def run_system(system_name):
    st.header(f"{system_name.upper()} Simulation")
    valves, pipes, png_path = load_system_data(system_name)
    if not valves or not pipes:
        st.error("Missing JSON data")
        return

    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = valves[tag].get("state","closed").lower()=="open"

    network = build_network(valves, pipes, system_name)
    pressurized_nodes = propagate_pressure(network, get_pressure_config(system_name)["pressure_sources"])
    for node in pressurized_nodes:
        if node.startswith("pipe_"):
            network[node]["pressurized"]=True

    # Sidebar valve controls
    with st.sidebar:
        st.header("🎛️ Valve Controls")
        for tag in valves:
            state = network[tag]["is_open"]
            label = f"{'🟢 OPEN' if state else '🔴 CLOSED'} {tag}"
            if st.button(label,key=f"valve_{system_name}_{tag}"):
                st.session_state.valve_states[tag] = not state
                st.rerun()

    col1,col2 = st.columns([3,1])
    with col1:
        image = render_pid(valves,pipes,png_path,system_name,network)
        st.image(image,use_container_width=True)
    with col2:
        st.header("Legend")
        st.write("🟢 Flowing (Valve Open)")
        st.write("🔵 Pressurized (Valve Closed)")
        st.write("🔴 Closed Valve")

# ================== NAVIGATION ==================
col1,col2,col3,col4,col5 = st.columns(5)
systems = ["mixing","supply","dgs","return","seal"]
for c,s in zip([col1,col2,col3,col4,col5],systems):
    with c:
        if st.button(s.upper()):
            st.session_state.current_system = s
            st.session_state.selected_pipe = None
            st.session_state.selected_valve = None
            st.rerun()

st.markdown("---")
if st.session_state.current_system=="home":
    st.title("🏠 Rig Simulation Dashboard")
    st.write("Select a system above to start.")
else:
    run_system(st.session_state.current_system)
