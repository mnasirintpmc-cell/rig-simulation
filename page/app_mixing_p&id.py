import streamlit as st
from PIL import Image, ImageDraw
import json
import os

# ===== Utility: find file =====
def find_file(filename, folders=["assets", "data", "."]):
    for f in folders:
        path = os.path.join(f, filename)
        if os.path.exists(path):
            return path
    return None

# ===== Load required files =====
PID_FILE = find_file("p&id_mixing.png")
VALVES_FILE = find_file("valves_mixing.json", ["data"])
PIPES_FILE = find_file("pipes_mixing.json", ["data"])

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}

valves_raw = load_json(VALVES_FILE)
pipes_raw = load_json(PIPES_FILE)

# Create dynamic pipe tags (P1, P2, P3…)
pipes = []
for idx, p in enumerate(pipes_raw):
    p["tag"] = f"P{idx+1}"
    pipes.append(p)

# Map valves to pipe tags
valves = {}
for tag, v in valves_raw.items():
    connected = []
    for k, lst in v.items():
        if k.endswith(".json") and isinstance(lst, list):
            for index in lst:
                if index > 0 and index <= len(pipes):
                    connected.append(pipes[index - 1]["tag"])
    valves[tag] = {
        "x": v["x"],
        "y": v["y"],
        "connected_pipes": connected
    }

# ---- Session State ----
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {v: False for v in valves}

# ---- Active pipes ----
def get_active_pipes():
    active = set()
    for vtag, vdata in valves.items():
        if st.session_state.valve_states.get(vtag):
            active.update(vdata["connected_pipes"])
    return active

# ---- Render P&ID ----
def render_pid():
    img = Image.open(PID_FILE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    active = get_active_pipes()

    # Draw pipes
    for p in pipes:
        tag = p["tag"]
        flowing = tag in active
        color = (0, 255, 0) if flowing else (60, 60, 100)
        draw.line([(p["x1"], p["y1"]), (p["x2"], p["y2"])],
                  fill=color, width=7 if flowing else 4)

    # Draw valves
    for tag, v in valves.items():
        x, y = v["x"], v["y"]
        color = (0, 255, 0) if st.session_state.valve_states[tag] else (255, 0, 0)
        draw.ellipse([x-12, y-12, x+12, y+12], fill=color, outline="white", width=3)

    return img.convert("RGB")

# ---- MAIN PAGE ----
def run():
    st.title("Mixing Area – P&ID Simulation")

    col_pid, col_controls = st.columns([4, 1])

    # --- FIXED P&ID (no scrolling) ---
    with col_pid:
        st.image(render_pid(), use_container_width=True)

    # --- SCROLLABLE VALVE CONTROLS ---
    with col_controls:
        st.markdown(
            """
            <div style="height:85vh; overflow-y:scroll; padding-right:10px;">
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Valve Controls")

        for tag in valves:
            current = st.session_state.valve_states[tag]
            if st.button(f"{'OPEN' if not current else 'CLOSE'} {tag}", key=tag):
                st.session_state.valve_states[tag] = not current
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
