import streamlit as st
import json
from PIL import Image
import os

st.set_page_config(layout="wide")
st.title("🎯 P&ID Marker Tool")

# Upload P&ID image
uploaded_file = st.file_uploader("Upload P&ID Image", type=['png', 'jpg', 'jpeg'])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True, caption="Click on valves and pipes")
    
    # Get image dimensions
    width, height = image.size
    st.write(f"Image size: {width} x {height}")
    
    # Initialize session state
    if 'valves' not in st.session_state:
        st.session_state.valves = {}
    if 'pipes' not in st.session_state:
        st.session_state.pipes = []
    if 'current_pipe' not in st.session_state:
        st.session_state.current_pipe = None
    
    # Valve marking
    st.subheader("🔘 Mark Valves")
    col1, col2 = st.columns(2)
    
    with col1:
        valve_id = st.text_input("Valve ID", "V-101")
        if st.button("Add Valve at Center"):
            st.session_state.valves[valve_id] = {"x": width//2, "y": height//2}
    
    with col2:
        if st.button("Clear All Valves"):
            st.session_state.valves = {}
    
    # Pipe marking
    st.subheader("📏 Mark Pipes")
    pipe_col1, pipe_col2 = st.columns(2)
    
    with pipe_col1:
        if st.button("Start New Pipe"):
            st.session_state.current_pipe = {"x1": width//4, "y1": height//4, "x2": width*3//4, "y2": height*3//4}
    
    with pipe_col2:
        if st.button("Clear All Pipes"):
            st.session_state.pipes = []
    
    # Manual coordinate input
    st.subheader("✏️ Manual Coordinates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Valve Coordinates**")
        for valve_id in list(st.session_state.valves.keys())[:5]:  # Show first 5
            x = st.number_input(f"{valve_id} X", value=st.session_state.valves[valve_id]["x"], key=f"vx_{valve_id}")
            y = st.number_input(f"{valve_id} Y", value=st.session_state.valves[valve_id]["y"], key=f"vy_{valve_id}")
            st.session_state.valves[valve_id] = {"x": x, "y": y}
    
    with col2:
        st.write("**Pipe Coordinates**")
        for i, pipe in enumerate(st.session_state.pipes[:5]):  # Show first 5 pipes
            st.write(f"Pipe {i+1}:")
            x1 = st.number_input(f"Start X", value=pipe["x1"], key=f"px1_{i}")
            y1 = st.number_input(f"Start Y", value=pipe["y1"], key=f"py1_{i}")
            x2 = st.number_input(f"End X", value=pipe["x2"], key=f"px2_{i}")
            y2 = st.number_input(f"End Y", value=pipe["y2"], key=f"py2_{i}")
            st.session_state.pipes[i] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    
    # Display current data
    st.subheader("📊 Current Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Valves:**")
        st.json(st.session_state.valves)
    
    with col2:
        st.write("**Pipes:**")
        st.json(st.session_state.pipes)
    
    # Export data
    st.subheader("💾 Export Data")
    system_name = st.text_input("System Name", "mixing")
    
    if st.button("Export JSON Files"):
        # Save valves
        with open(f"data/valves_{system_name}.json", 'w') as f:
            json.dump(st.session_state.valves, f, indent=2)
        
        # Save pipes
        with open(f"data/pipes_{system_name}.json", 'w') as f:
            json.dump(st.session_state.pipes, f, indent=2)
        
        st.success(f"✅ Exported valves_{system_name}.json and pipes_{system_name}.json")
