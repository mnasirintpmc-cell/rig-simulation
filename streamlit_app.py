# Updated Calibration Tools section in the run_simulation function
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
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Valve Controls")
        for tag in valves:
            state = st.session_state.valve_states[tag]
            label = f"{'🟢 OPEN' if state else '🔴 CLOSED'} {tag}"
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
                
                if st.button("💾 Update Valve Position", key="update_valve", use_container_width=True):
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
                
                if st.button("💾 Update Pipe Position", key="update_pipe", use_container_width=True):
                    pipes[st.session_state.selected_pipe] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                    save_system_data(system_name, valves, pipes)
                    st.success("✅ Pipe position updated!")
                    st.rerun()
            
            # Deselect button
            if st.button("❌ Deselect All", key="deselect_all", use_container_width=True):
                st.session_state.selected_valve = None
                st.session_state.selected_pipe = None
                st.rerun()
        
        else:
            st.info("🔧 Enable calibration to adjust positions")
        
        st.header("📊 Status")
        open_valves = sum(st.session_state.valve_states.values())
        st.metric("Open Valves", open_valves)
        st.metric("Total Valves", len(valves))
        st.metric("Total Pipes", len(pipes))
        
        # Clear all valves button
        if st.button("🔄 Clear All Valves", key="clear_valves", use_container_width=True):
            for tag in valves:
                st.session_state.valve_states[tag] = False
            st.rerun()
    
    # Main display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        image = render_pid_with_overlay(valves, pipes, png_path, display_names[system_name])
        st.image(image, use_container_width=True, 
                caption=f"{display_names[system_name]} - Purple=Selected | Green=Flow | Red=Closed")
    
    with col2:
        st.header("🎯 Legend")
        st.write("🟣 **Purple**: Selected for calibration")
        st.write("🟢 **Green pipes/valves**: Flow/Open")
        st.write("🔵 **Blue pipes**: No flow")
        st.write("🔴 **Red valves**: Closed")
        st.write("---")
        st.info("💡 **Enable Calibration** to adjust positions")
        st.info("💡 **Select items** to make them purple")
        st.info("💡 **Move to Center** for easy positioning")
