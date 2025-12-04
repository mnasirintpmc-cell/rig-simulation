# app_mixing_p&id.py
import streamlit as st
from PIL import Image, ImageDraw
import json, os

def run():
    st.title("Rig Simulation – Mixing Area")

    # ===================== FILE PATHS =====================
    PID_FILE = os.path.join("assets", "p&id_mixing.png")
    VALVES_FILE = os.path.join("data", "valves_mixing.json")
    PIPES_FILE = os.path.join("data", "pipes_mixing.json")

    if not all([os.path.exists(PID_FILE), os.path.exists(VALVES_FILE), os.path.exists(PIPES_FILE)]):
        st.error("❌ Missing required files!")
        st.stop()

    # ===================== LOAD JSON =====================
    with open(PIPES_FILE) as f:
        pipes_raw = json.load(f)
    with open(VALVES_FILE) as f:
        valves_raw = json.load(f)

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
        valves[v_tag] = {
            "x": vdata.get("x", 0),
            "y": vdata.get("y", 0),
            "connected_pipes": connected_tags,
            "state": vdata.get("state", "Closed")
        }

    # ===================== SESSION STATE =====================
    if "valve_states" not in st.session_state:
        st.session_state.valve_states = {tag: False for tag in valves}

    # ===================== ACTIVE PIPES =====================
    def get_active_pipes():
        active = set()
        for v_tag, vdata in valves.items():
            if st.session_state.valve_states.get(v_tag, False):
                active.update(vdata["connected_pipes"])
        return active

    # ===================== RENDER P&ID =====================
    def render_pid():
        try:
            img = Image.open(PID_FILE).convert("RGBA")
        except:
            img = Image.new("RGBA", (800, 600), (50, 50, 50))
            draw = ImageDraw.Draw(img)
            draw.text((100, 300), f"Missing {PID_FILE}", fill="white")
            return img.convert("RGB")

        draw = ImageDraw.Draw(img)
        active_pipes = get_active_pipes()

        # Draw pipes
        for pipe in pipes:
            p_tag = pipe["tag"]
            color = (0,255,0) if p_tag in active_pipes else (60,60,100)
            width = 7 if p_tag in active_pipes else 4
            draw.line([(pipe["x1"], pipe["y1"]),(pipe["x2"], pipe["y2"])], fill=color, width=width)

        # Draw valves
        for v_tag, vdata in valves.items():
            x, y = vdata["x"], vdata["y"]
            color = (0,255,0) if st.session_state.valve_states.get(v_tag, False) else (255,0,0)
            draw.ellipse([x-12,y-12,x+12,y+12], fill=color, outline="white", width=3)
            draw.text((x+15,y-15), v_tag, fill="white", stroke_fill="black", stroke_width=2)

        return img.convert("RGB")

    # ===================== SIDEBAR VALVE CONTROLS =====================
    st.sidebar.header("Valve Controls")
    for v_tag in valves:
        state = st.session_state.valve_states.get(v_tag, False)
        label = f"{'OPEN' if state else 'CLOSED'} {v_tag}"
        if st.sidebar.button(label, key=f"valve_{v_tag}"):
            st.session_state.valve_states[v_tag] = not state
            st.experimental_rerun()

    # ===================== SHOW P&ID =====================
    st.image(render_pid(), use_column_width=True, caption="Valve status on P&ID")
