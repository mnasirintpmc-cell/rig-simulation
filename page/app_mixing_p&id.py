# app_mixing_p&id.py
# Wrap your previous mixing page code in a function

import streamlit as st
from PIL import Image, ImageDraw
import json, os

def run():
    st.title("Rig Simulation – Mixing Area")

    # ===================== FILE PATHS =====================
    def find_file(filename, folders=["assets", "data", "."]):
        for f in folders:
            path = os.path.join(f, filename)
            if os.path.exists(path):
                return path
        return None

    PID_FILE = find_file("p&id_mixing.png", ["assets"])
    VALVES_FILE = find_file("valves_mixing.json", ["data"])
    PIPES_FILE = find_file("pipes_mixing.json", ["data"])

    if not all([PID_FILE, VALVES_FILE, PIPES_FILE]):
        st.error("❌ Missing required files!")
        st.stop()

    # ===================== LOAD JSON =====================
    def load_json(file):
        try:
            with open(file) as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading {file}: {e}")
            return {} if "valves" in file else []

    valves_raw = load_json(VALVES_FILE)
    pipes_raw = load_json(PIPES_FILE)

    # ===================== DYNAMIC PIPE TAGS =====================
    pipes = []
    for idx, pipe in enumerate(pipes_raw):
        pipe["tag"] = f"P{idx+1}"
        pipes.append(pipe)

    # ===================== MAP VALVES TO PIPE TAGS =====================
    valves = {}
    for v_tag, vdata in valves_raw.items():
        connected_tags = []
        for key, indices in vdata.items():
            if key.endswith(".json") and isinstance(indices, list):
                for i in indices:
                    if isinstance(i, int) and 1 <= i <= len(pipes):
                        connected_tags.append(pipes[i-1]["tag"])
                    else:
                        connected_tags.append(None)
                        st.warning(f"Valve {v_tag} references invalid pipe index {i} in {key}")
        valves[v_tag] = {
            "x": vdata.get("x", 0),
            "y": vdata.get("y", 0),
            "connected_pipes": connected_tags,
            "state": vdata.get("state", "Closed")
        }

    # ===================== SESSION STATE =====================
    if "valve_states" not in st.session_state:
        st.session_state.valve_states = {tag: False for tag in valves}
    if "selected_pipe" not in st.session_state:
        st.session_state.selected_pipe = None

    # ===================== PIPE STATUS =====================
    def get_active_pipes():
        active = set()
        for v_tag, vdata in valves.items():
            if st.session_state.valve_states.get(v_tag, False):
                active.update([p for p in vdata["connected_pipes"] if p])
        return active

    def get_pipe_status(pipe_tag, active_pipes):
        has_flow = pipe_tag in active_pipes
        has_pressure = has_flow
        return has_flow, has_pressure

    # ===================== RENDER SYSTEM =====================
    def render_system():
        try:
            img = Image.open(PID_FILE).convert("RGBA")
        except:
            img = Image.new("RGBA", (800, 600), (50, 50, 50))
            draw = ImageDraw.Draw(img)
            draw.text((100, 300), f"Missing {PID_FILE}", fill="white")
            return img.convert("RGB")

        draw = ImageDraw.Draw(img)
        active_pipes = get_active_pipes()

        for pipe in pipes:
            p_tag = pipe["tag"]
            has_flow, _ = get_pipe_status(p_tag, active_pipes)
            if st.session_state.selected_pipe == p_tag:
                color, width = (180,0,255), 9
            elif has_flow:
                color, width = (0,255,0), 7
            else:
                color, width = (60,60,100), 4
            draw.line([(pipe["x1"], pipe["y1"]),(pipe["x2"], pipe["y2"])], fill=color, width=width)

        for v_tag, vdata in valves.items():
            x, y = vdata["x"], vdata["y"]
            color = (0,255,0) if st.session_state.valve_states.get(v_tag, False) else (255,0,0)
            draw.ellipse([x-12,y-12,x+12,y+12], fill=color, outline="white", width=3)
            draw.text((x+15,y-15), v_tag, fill="white", stroke_fill="black", stroke_width=2)

        return img.convert("RGB")

    # ===================== UI =====================
    with st.sidebar:
        st.header("Valve Controls")
        for v_tag in valves:
            state = st.session_state.valve_states.get(v_tag, False)
            label = f"{'OPEN' if state else 'CLOSED'} {v_tag}"
            if st.button(label, key=f"valve_{v_tag}", use_container_width=True):
                st.session_state.valve_states[v_tag] = not state
                st.rerun()

        st.markdown("---")
        st.header("Pipe Selection")
        if st.button("Unselect Pipe", use_container_width=True):
            st.session_state.selected_pipe = None
            st.rerun()
        for pipe in pipes:
            p_tag = pipe["tag"]
            icon = "Selected" if st.session_state.selected_pipe == p_tag else "Pipe"
            if st.button(f"{icon} {p_tag}", key=f"pipe_{p_tag}", use_container_width=True):
                st.session_state.selected_pipe = p_tag
                st.rerun()

    col1, col2 = st.columns([3,1])
    with col1:
        st.image(render_system(), use_container_width=True,
                 caption="🟢 Flowing | ⚫ Empty | 🟣 Selected")

    with col2:
        st.header("Live Status")
        active_pipes = get_active_pipes()
        st.metric("Active Pipes", len(active_pipes))
        open_valves = sum(1 for v in st.session_state.valve_states.values() if v)
        st.metric("Open Valves", f"{open_valves}/{len(valves)}")
        st.markdown("---")
        st.header("Active Pipe Details")
        for pipe in pipes:
            p_tag = pipe["tag"]
            if p_tag in active_pipes:
                controlling = [v_tag for v_tag, vdata in valves.items()
                               if st.session_state.valve_states.get(v_tag, False) and p_tag in vdata["connected_pipes"]]
                st.write(f"• Pipe {p_tag} ← {', '.join(controlling)}")
