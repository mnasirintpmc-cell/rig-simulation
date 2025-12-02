# streamlit_app.py - Full Corrected Version with Proper Valve-Driven Flow
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(page_title="Rig Simulation Dashboard", page_icon="🏭", layout="wide")

# ================== SESSION STATE ==================
if 'current_system' not in st.session_state:
    st.session_state.current_system = "home"
if 'valve_states' not in st.session_state:
    st.session_state.valve_states = {}
if 'selected_pipe' not in st.session_state:
    st.session_state.selected_pipe = None
if 'selected_valve' not in st.session_state:
    st.session_state.selected_valve = None

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

# ================== LOAD DATA ==================
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

    # Initialize valve states if not present
    for tag in valves:
        if tag not in st.session_state.valve_states:
            state = valves[tag].get("state","closed")
            st.session_state.valve_states[tag] = state.lower() == "open"

    return valves, pipes, png_path

# ================== BUILD NETWORK ==================
def build_network(valves, pipes, system_name):
    network = {}
    # Add pipes
    for i, pipe in enumerate(pipes):
        network[f"pipe_{i}"] = {"type":"pipe","connected_valves":[],"pressurized":False,"flowing":False}

    # Add valves
    for tag, vdata in valves.items():
        connected_pipes = []
        # Gather all system-specific pipe lists
        for k,v in vdata.items():
            if k.endswith(".json"):
                connected_pipes.extend(v)
        network[tag] = {
            "type":"valve",
            "connected_pipes":connected_pipes,
            "is_open": st.session_state.valve_states.get(tag, False),
            "is_special": tag in get_pressure_config(system_name)["special_valves"]
        }
        # Link pipes to this valve
        for pi in connected_pipes:
            pid = f"pipe_{pi}"
            if pid in network:
                network[pid]["connected_valves"].append(tag)
    return network

# ================== PROPAGATE PRESSURE ==================
def propagate_pressure(network, pressure_sources):
    pressurized = set()
    flowing = set()

    # Initialize pressure sources
    for src in pressure_sources:
        pid = f"pipe_{src-1}"  # JSON uses 0-indexed pipe IDs
        pressurized.add(pid)

    changed = True
    while changed:
        changed = False
        for nid, node in network.items():
            if nid in pressurized:
                if node["type"]=="pipe":
                    for v in node["connected_valves"]:
                        vdata = network[v]
                        if not vdata["is_special"] or vdata["is_open"]:
                            if v not in pressurized:
                                pressurized.add(v)
                                changed = True
                elif node["type"]=="valve" and node["is_open"]:
                    for pi in node["connected_pipes"]:
                        pid = f"pipe_{pi}"
                        if pid not in pressurized:
                            pressurized.add(pid)
                            flowing.add(pid)
                            changed = True
    return pressurized, flowing

def get_pipe_status(pipe_idx, pressurized_nodes, flowing_nodes):
    pid = f"pipe_{pipe_idx}"
    has_pressure = pid in pressurized_nodes
    has_flow = pid in flowing_nodes
    return has_pressure, has_flow

# ================== RENDER P&ID ==================
def render_pid(valves, pipes, png_path, pressurized_nodes, flowing_nodes):
    try:
        img = Image.open(png_path).convert("RGBA")
    except:
        img = Image.new("RGBA",(800,600),(40,40,60))
    draw = ImageDraw.Draw(img)

    # Draw pipes
    for i, pipe in enumerate(pipes):
        hp,hf = get_pipe_status(i, pressurized_nodes, flowing_nodes)
        color = (0,255,0) if hf else (100,180,255) if hp else (100,100,255)
        width = 6 if hf else 5 if hp else 4
        draw.line([(pipe["x1"],pipe["y1"]),(pipe["x2"],pipe["y2"])],fill=color,width=width)

    # Draw valves
    for tag,vdata in valves.items():
        is_open = st.session_state.valve_states.get(tag, False)
        x,y = vdata["x"],vdata["y"]
        radius = 5
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

    network = build_network(valves, pipes, system_name)
    pressurized, flowing = propagate_pressure(network, get_pressure_config(system_name)["pressure_sources"])

    # Sidebar valve controls
    with st.sidebar:
        st.header("🎛️ Valve Controls")
        for tag in valves:
            state = st.session_state.valve_states[tag]
            label = f"{'🟢 OPEN' if state else '🔴 CLOSED'} {tag}"
            if st.button(label,key=f"valve_{system_name}_{tag}"):
                st.session_state.valve_states[tag] = not state
                st.rerun()
        st.metric("Pressurized Pipes", sum(pid in pressurized for pid in network if network[pid]["type"]=="pipe"))
        st.metric("Flowing Pipes", sum(pid in flowing for pid in network if network[pid]["type"]=="pipe"))

    # Main display
    col1,col2 = st.columns([3,1])
    with col1:
        image = render_pid(valves, pipes, png_path, pressurized, flowing)
        st.image(image,use_container_width=True)
    with col2:
        st.header("Legend")
        st.write("🟢 Flowing pipes")
        st.write("🔵 Pressurized pipes")
        st.write("🔴 Closed valves")

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
