# streamlit_app.py - FIXED PIPE SELECTION
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(
    page_title="Rig Simulation",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if 'current_system' not in st.session_state:
    st.session_state.current_system = "home"
if 'valve_states' not in st.session_state:
    st.session_state.valve_states = {}
if 'active_pipes' not in st.session_state:
    st.session_state.active_pipes = {}
if 'selected_pipes' not in st.session_state:
    st.session_state.selected_pipes = []
if 'selected_valve_for_pipes' not in st.session_state:
    st.session_state.selected_valve_for_pipes = None
if 'show_pipe_selector' not in st.session_state:
    st.session_state.show_pipe_selector = False

# System files mapping
SYSTEM_FILES = {
    "mixing": {
        "name": "Mixing System",
        "valves": "data/valves_mixing.json",
        "pipes": "data/pipes_mixing.json",
        "image": "assets/p&id_mixing.png"
    },
    "supply": {
        "name": "Pressure Supply", 
        "valves": "data/valves_pressure_in.json",
        "pipes": "data/pipes_pressure_in.json",
        "image": "assets/p&id_pressure_in.png"
    },
    "dgs": {
        "name": "DGS System",
        "valves": "data/valves_dgs.json",
        "pipes": "data/pipes_dgs.json", 
        "image": "assets/p&id_dgs.png"
    },
    "return": {
        "name": "Pressure Return",
        "valves": "data/valves_pressure_return.json",
        "pipes": "data/pipes_pressure_return.json",
        "image": "assets/p&id_pressure_return.png"
    },
    "seal": {
        "name": "Separation Seal",
        "valves": "data/valves_separation_seal.json",
        "pipes": "data/pipes_separation_seal.json",
        "image": "assets/p&id_separation_seal.png"
    }
}

# ==================== LOAD DATA ====================
def load_data(system):
    """Load valves and pipes for a system"""
    config = SYSTEM_FILES[system]
    
    # Load valves
    valves = {}
    if os.path.exists(config["valves"]):
        with open(config["valves"], 'r') as f:
            valves = json.load(f)
    else:
        st.error(f"Missing valves file: {config['valves']}")
    
    # Load pipes
    pipes = []
    if os.path.exists(config["pipes"]):
        with open(config["pipes"], 'r') as f:
            pipes = json.load(f)
    else:
        st.error(f"Missing pipes file: {config['pipes']}")
    
    return valves, pipes, config["image"]

def save_valves(system, valves):
    """Save valves back to file"""
    config = SYSTEM_FILES[system]
    with open(config["valves"], 'w') as f:
        json.dump(valves, f, indent=2)

# ==================== DIRECT MAPPING LOGIC ====================
def get_pipe_status(pipe_index, valves, valve_states):
    pipe_display_num = pipe_index + 1
    
    for valve_tag, valve_data in valves.items():
        if valve_states.get(valve_tag, False):
            connected_pipes = valve_data.get("connected_pipes", [])
            if pipe_display_num in connected_pipes:
                return "active"
    
    return "inactive"

# ==================== SIMPLE RENDER ====================
def render_system(valves, pipes, image_path, system_name):
    """Render with DIRECT valve-to-pipe mapping"""
    # Load image
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 600), (50, 50, 70))
    
    draw = ImageDraw.Draw(img)
    
    # Draw all pipes first
    for i, pipe in enumerate(pipes):
        status = get_pipe_status(i, valves, st.session_state.valve_states)
        
        if status == "active":
            color = (0, 255, 0)  # GREEN - controlled by open valve
            width = 8
        else:
            color = (100, 100, 100)  # GRAY - inactive
            width = 4
        
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                 fill=color, width=width)
        
        # Label pipe number
        mid_x = (pipe["x1"] + pipe["x2"]) // 2
        mid_y = (pipe["y1"] + pipe["y2"]) // 2
        draw.text((mid_x, mid_y), str(i+1), fill="white")
    
    # Draw valves on top - YOUR EXACT SIZE [x-10, y-10, x+10, y+10]
    for valve_tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(valve_tag, False)
        
        # Valve color
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)
        
        # Draw valve - YOUR EXACT SIZE
        draw.ellipse([x-10, y-10, x+10, y+10],  # ← FIXED TO YOUR SIZE
                    fill=valve_color, outline="white", width=3)
        
        # Show connected pipe count
        connected = valve_data.get("connected_pipes", [])
        if connected:
            draw.text((x-6, y-8), str(len(connected)), 
                     fill="white", stroke_fill="black")
        
        # Valve label
        draw.text((x+15, y-12), valve_tag, 
                 fill="white", stroke_fill="black")
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation - Direct Valve Control")
    st.markdown("### Click a system to toggle valves and see EXACT pipe connections")
    
    cols = st.columns(5)
    systems = [
        ("mixing", "🔧", "Mixing"),
        ("supply", "⚡", "Supply"),
        ("dgs", "🎮", "DGS"),
        ("return", "🔄", "Return"),
        ("seal", "🔒", "Seal")
    ]
    
    for idx, (sys_id, icon, name) in enumerate(systems):
        with cols[idx]:
            if st.button(f"{icon}\n**{name}**", use_container_width=True):
                st.session_state.current_system = sys_id
                st.rerun()
    
    st.markdown("---")
    st.info("**How it works:** Each valve JSON has a 'connected_pipes' list. When you open a valve, ONLY those specific pipes turn GREEN.")

# ==================== SYSTEM PAGE ====================
else:
    system = st.session_state.current_system
    config = SYSTEM_FILES[system]
    
    # Load data
    valves, pipes, image_path = load_data(system)
    
    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Header
    st.title(f"{config['name']}")
    
    if st.button("← Back to Home"):
        st.session_state.current_system = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Two column layout
    col_viz, col_controls = st.columns([3, 1])
    
    with col_controls:
        st.header("🎛️ Valve Controls")
        
        # Show valve connection info
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected_pipes = valve_data.get("connected_pipes", [])
            
            # Button with clear status
            if is_open:
                btn_text = f"🟢 OPEN: {tag}"
            else:
                btn_text = f"🔴 CLOSED: {tag}"
            
            col_btn, col_info = st.columns([2, 1])
            
            with col_btn:
                if st.button(btn_text, key=f"btn_{tag}", use_container_width=True):
                    st.session_state.valve_states[tag] = not is_open
                    st.rerun()
            
            with col_info:
                if connected_pipes:
                    st.write(f"→ {len(connected_pipes)} pipes")
                
                # Small button to select this valve for pipe assignment
                if st.button("📝", key=f"select_{tag}", help=f"Select {tag} for pipe assignment"):
                    st.session_state.selected_valve_for_pipes = tag
                    st.session_state.show_pipe_selector = True
                    st.rerun()
        
        st.markdown("---")
        st.header("📊 Live Status")
        
        # Calculate active pipes
        active_count = 0
        for i in range(len(pipes)):
            if get_pipe_status(i, valves, st.session_state.valve_states) == "active":
                active_count += 1
        
        open_valves = sum(1 for v in st.session_state.valve_states.values() if v)
        
        st.metric("Active Pipes", active_count)
        st.metric("Open Valves", f"{open_valves}/{len(valves)}")
        
        # Control buttons
        st.markdown("---")
        st.header("⚙️ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Open ALL", use_container_width=True):
                for tag in valves:
                    st.session_state.valve_states[tag] = True
                st.rerun()
        
        with col2:
            if st.button("Close ALL", use_container_width=True):
                for tag in valves:
                    st.session_state.valve_states[tag] = False
                st.rerun()
        
        # Show connection details
        st.markdown("---")
        st.header("🔗 Connections")
        
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected = valve_data.get("connected_pipes", [])
            
            if connected:
                status = "🟢" if is_open else "🔴"
                st.write(f"{status} **{tag}** → Pipes: {connected}")
    
    with col_viz:
        # Render and display
        if os.path.exists(image_path):
            img = render_system(valves, pipes, image_path, system)
            st.image(img, use_container_width=True, 
                    caption="🟢 GREEN pipes = Controlled by OPEN valves | 🔴 RED valve = CLOSED | 🟢 GREEN valve = OPEN")
        else:
            st.error(f"Image not found: {image_path}")
            with st.expander("🔍 Debug: Show loaded data"):
                st.write("**Valves (first 3):**")
                for tag, data in list(valves.items())[:3]:
                    st.json({tag: data})
                st.write("**Pipes (first 3):**")
                st.json(pipes[:3] if pipes else [])
        
        # Active pipes list
        st.markdown("---")
        st.subheader("✅ Active Pipes (Green)")
        
        active_list = []
        for i in range(len(pipes)):
            if get_pipe_status(i, valves, st.session_state.valve_states) == "active":
                controlling_valves = []
                for tag, valve_data in valves.items():
                    if st.session_state.valve_states.get(tag, False):
                        connected = valve_data.get("connected_pipes", [])
                        if (i+1) in connected:
                            controlling_valves.append(tag)
                
                if controlling_valves:
                    active_list.append(f"**Pipe {i+1}** ← {', '.join(controlling_valves)}")
        
        if active_list:
            for item in active_list:
                st.write(f"• {item}")
        else:
            st.write("No active pipes. Open valves to activate their connected pipes.")

# ==================== PIPE SELECTION TOOL ====================
with st.sidebar:
    st.title("🔧 Pipe Connection Tool")
    
    # Toggle visibility
    if st.button("🔧 Show/Hide Pipe Selector"):
        st.session_state.show_pipe_selector = not st.session_state.show_pipe_selector
        st.rerun()
    
    if st.session_state.show_pipe_selector and st.session_state.current_system != "home":
        st.warning("🛠️ **PIPE SELECTION ACTIVE**")
        
        if st.session_state.selected_valve_for_pipes:
            st.subheader(f"🔧 Configuring: {st.session_state.selected_valve_for_pipes}")
            
            # Show current connections
            current_valve = valves.get(st.session_state.selected_valve_for_pipes, {})
            current_pipes = current_valve.get("connected_pipes", [])
            st.write(f"**Currently controls:** {current_pipes}")
            
            # Pipe selection grid - ALL PIPES
            st.subheader("📋 Select Pipes (Click to toggle)")
            
            # Create a grid of buttons
            cols_per_row = 4
            pipe_buttons = []
            
            for i in range(len(pipes)):
                pipe_num = i + 1
                is_selected = pipe_num in st.session_state.selected_pipes
                
                # Create button
                if st.button(f"{'✅' if is_selected else '⬜'} Pipe {pipe_num}", 
                           key=f"select_pipe_{pipe_num}",
                           use_container_width=True):
                    if pipe_num in st.session_state.selected_pipes:
                        st.session_state.selected_pipes.remove(pipe_num)
                    else:
                        st.session_state.selected_pipes.append(pipe_num)
                    st.rerun()
            
            # Show selected pipes
            if st.session_state.selected_pipes:
                st.write(f"**Selected pipes:** {sorted(st.session_state.selected_pipes)}")
                
                # Action buttons
                st.subheader("💾 Save Connections")
                
                col_add, col_replace = st.columns(2)
                with col_add:
                    if st.button("➕ Add Selected", use_container_width=True):
                        # Add pipes to valve
                        if "connected_pipes" not in current_valve:
                            current_valve["connected_pipes"] = []
                        
                        for pipe_num in st.session_state.selected_pipes:
                            if pipe_num not in current_valve["connected_pipes"]:
                                current_valve["connected_pipes"].append(pipe_num)
                        
                        valves[st.session_state.selected_valve_for_pipes] = current_valve
                        save_valves(system, valves)
                        st.success(f"Added pipes {sorted(st.session_state.selected_pipes)}")
                        st.session_state.selected_pipes = []
                        st.rerun()
                
                with col_replace:
                    if st.button("🔄 Replace All", use_container_width=True):
                        # Replace all pipes
                        current_valve["connected_pipes"] = sorted(st.session_state.selected_pipes)
                        valves[st.session_state.selected_valve_for_pipes] = current_valve
                        save_valves(system, valves)
                        st.success(f"Now controls pipes {sorted(st.session_state.selected_pipes)}")
                        st.session_state.selected_pipes = []
                        st.rerun()
                
                if st.button("🗑️ Clear All", use_container_width=True):
                    # Clear all connections
                    current_valve["connected_pipes"] = []
                    valves[st.session_state.selected_valve_for_pipes] = current_valve
                    save_valves(system, valves)
                    st.success("Cleared all pipe connections")
                    st.session_state.selected_pipes = []
                    st.rerun()
            
            # Quick select buttons
            st.subheader("⚡ Quick Select")
            col_q1, col_q2, col_q3 = st.columns(3)
            with col_q1:
                if st.button("1-5", key="q1"):
                    st.session_state.selected_pipes = [1, 2, 3, 4, 5]
                    st.rerun()
            with col_q2:
                if st.button("6-10", key="q2"):
                    st.session_state.selected_pipes = [6, 7, 8, 9, 10]
                    st.rerun()
            with col_q3:
                if st.button("Clear", key="q3"):
                    st.session_state.selected_pipes = []
                    st.rerun()
            
            # Finish button
            if st.button("✅ Done Configuring", use_container_width=True):
                st.session_state.selected_valve_for_pipes = None
                st.session_state.show_pipe_selector = False
                st.session_state.selected_pipes = []
                st.rerun()
        
        else:
            st.info("👆 Click the 📝 button next to a valve in the main panel to select it for pipe configuration")
            
            # Show all valve connections
            st.subheader("📋 Current Valve Connections")
            for tag, data in valves.items():
                connected = data.get("connected_pipes", [])
                if connected:
                    st.write(f"**{tag}**: {connected}")
                else:
                    st.write(f"**{tag}**: ❌ No pipes")
    
    elif not st.session_state.show_pipe_selector:
        st.info("🔧 Pipe selector is hidden. Click 'Show/Hide Pipe Selector' to configure valve-pipe connections.")

# ==================== DEBUG INFO ====================
with st.sidebar:
    if st.session_state.current_system != "home" and not st.session_state.show_pipe_selector:
        st.title("🔍 Quick Debug")
        
        if st.button("Test Pipe 1 Connection"):
            controlling = []
            for tag, data in valves.items():
                connected = data.get("connected_pipes", [])
                if 1 in connected:
                    controlling.append(tag)
            
            if controlling:
                st.success(f"✅ Pipe 1 controlled by: {controlling}")
            else:
                st.error("❌ Pipe 1 not controlled by any valve")
                st.info("Use the Pipe Connection Tool to add pipes to valves")
