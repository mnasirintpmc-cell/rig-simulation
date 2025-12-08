# pages/app_mixing_p&id.py - FIXED VERSION
import streamlit as st
from utils import find_file, load_json, render_system_image, get_pipe_status

st.set_page_config(layout="wide", page_title="Mixing Area")

# Load data
PID = find_file("p&id_mixing.png") or "assets/p&id_mixing.png"
VALVES = find_file("valves_mixing.json", ["data", "."]) or "data/valves_mixing.json"
PIPES = find_file("pipes_mixing.json", ["data", "."]) or "data/pipes_mixing.json"

valves = load_json(VALVES)
pipes = load_json(PIPES)

# Session defaults
if "valve_states" not in st.session_state:
    st.session_state.valve_states = {
        k: (valves[k].get("state", "Closed").lower() == "open") 
        for k in valves
    }
if "selected_pipe" not in st.session_state:
    st.session_state.selected_pipe = None

st.title("Mixing Area")

with st.sidebar:
    st.header("Valve Controls")
    for tag in valves:
        s = st.session_state.valve_states.get(tag, False)
        if st.button(f"{'🟢 OPEN' if s else '🔴 CLOSED'} {tag}", key=tag):
            st.session_state.valve_states[tag] = not s
            st.rerun()
    
    st.markdown("---")
    st.header("Pipe Selection")
    if st.button("Unselect", key="unselect"):
        st.session_state.selected_pipe = None
        st.rerun()
    for i in range(len(pipes)):
        if st.button(f"Pipe {i+1}", key=f"p{i}"):
            st.session_state.selected_pipe = i
            st.rerun()

# Render
img = render_system_image(
    PID, pipes, valves, st.session_state.valve_states, 
    selected_pipe=st.session_state.selected_pipe
)

col1, col2 = st.columns([3, 1])
with col1:
    st.image(img, use_container_width=True, caption="Mixing System P&ID")
with col2:
    st.header("Live Status")
    
    # FIXED: Calculate active pipes correctly
    active_pipes = 0
    for i in range(len(pipes)):
        has_flow, has_pressure = get_pipe_status(
            i, pipes, valves, st.session_state.valve_states
        )
        if has_flow:
            active_pipes += 1
    
    open_valves = sum(1 for state in st.session_state.valve_states.values() if state)
    
    st.metric("Active Pipes", active_pipes)
    st.metric("Open Valves", f"{open_valves}/{len(valves)}")
    
    # Show active pipes list
    st.markdown("---")
    st.subheader("Active Pipes")
    if active_pipes > 0:
        for i in range(len(pipes)):
            has_flow, _ = get_pipe_status(i, pipes, valves, st.session_state.valve_states)
            if has_flow:
                st.write(f"• **Pipe {i+1}**")
    else:
        st.write("No active pipes")

st.success("Mixing area loaded — use sidebar controls to toggle valves.")
