# pages/01_Mixing.py
import streamlit as st

# This imports the REAL rendering engine from your main file
render_cached = st.session_state.render_cached
get_system_files = st.session_state.get_system_files
load_system_data = st.session_state.load_system_data
save_system_data = st.session_state.save_system_data

st.title("Mixing Area")

system = "mixing"
valves, pipes, png = load_system_data(system)

# Initialize valves
for tag in valves:
    st.session_state.valve_states.setdefault(tag, False)

# Sidebar controls
with st.sidebar:
    st.header("Valve Controls")
    for tag in valves:
        if st.button(f"{'OPEN' if st.session_state.valve_states[tag] else 'CLOSED'} {tag}", 
                     key=f"{system}_{tag}", use_container_width=True):
            st.session_state.valve_states[tag] = not st.session_state.valve_states[tag]
            st.rerun()

    if st.button("Toggle Calibration", use_container_width=Trueaf=True):
        st.session_state.calibration_mode = not st.session_state.calibration_mode
        st.rerun()

    # Reuse calibration from main file (just call the function)
    if st.session_state.get("calibration_mode", False):
        st.warning("CALIBRATION MODE")
        # You can reuse the calibration code or import it
        # Or just say: "Use main page for calibration"

col1, col2 = st.columns([3,1])
with col1:
    img = render_cached(valves, pipes, png,
                       st.session_state.valve_states,
                       st.session_state.selected_pipe,
                       st.session_state.selected_valve)
    st.image(img, use_container_width=True)

with col2:
    st.metric("Open Valves", sum(st.session_state.valve_states.get(t, False) for t in valves))
