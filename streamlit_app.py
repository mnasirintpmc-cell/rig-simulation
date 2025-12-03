# streamlit_app.py - FIXED VALVE-TO-PIPE TOGGLING
import streamlit as st
from PIL import Image, ImageDraw
import json
import os

st.set_page_config(
    page_title="Rig Simulation Dashboard",
    page_icon="🏭",
    layout="wide"
)

# ==================== SESSION STATE ====================
if 'current_system' not in st.session_state:
    st.session_state.current_system = "home"
if 'valve_states' not in st.session_state:
    st.session_state.valve_states = {}
if 'active_pipes' not in st.session_state:
    st.session_state.active_pipes = set()

# ==================== SYSTEM CONFIGURATION ====================
SYSTEM_CONFIG = {
    "mixing": {
        "display_name": "Mixing Area",
        "valves_file": "data/valves_mixing.json",
        "pipes_file": "data/pipes_mixing.json", 
        "image_file": "assets/p&id_mixing.png",
        "pressure_sources": [1, 5]
    },
    "supply": {
        "display_name": "Pressure Supply",
        "valves_file": "data/valves_pressure_in.json",
        "pipes_file": "data/pipes_pressure_in.json",
        "image_file": "assets/p&id_pressure_in.png",
        "pressure_sources": [1, 3, 7]
    },
    "dgs": {
        "display_name": "DGS Simulation",
        "valves_file": "data/valves_dgs.json",
        "pipes_file": "data/pipes_dgs.json",
        "image_file": "assets/p&id_dgs.png",
        "pressure_sources": [1, 6, 11]
    },
    "return": {
        "display_name": "Pressure Return",
        "valves_file": "data/valves_pressure_return.json",
        "pipes_file": "data/pipes_pressure_return.json",
        "image_file": "assets/p&id_pressure_return.png",
        "pressure_sources": [2, 8]
    },
    "seal": {
        "display_name": "Separation Seal",
        "valves_file": "data/valves_separation_seal.json",
        "pipes_file": "data/pipes_separation_seal.json",
        "image_file": "assets/p&id_separation_seal.png",
        "pressure_sources": [1, 4, 9]
    }
}

# ==================== FILE LOADING ====================
def load_system_data(system_name):
    """Load valves, pipes, and image for a system"""
    config = SYSTEM_CONFIG.get(system_name)
    if not config:
        return {}, [], None
    
    valves, pipes, image = {}, [], None
    
    # Load valves
    valves_file = config["valves_file"]
    if os.path.exists(valves_file):
        try:
            with open(valves_file, 'r') as f:
                valves = json.load(f)
                # Ensure each valve has connected_pipes field
                for tag, data in valves.items():
                    if "connected_pipes" not in data:
                        data["connected_pipes"] = []
        except Exception as e:
            st.sidebar.error(f"Failed to load {valves_file}: {e}")
    else:
        st.sidebar.warning(f"Missing: {valves_file}")
    
    # Load pipes
    pipes_file = config["pipes_file"]
    if os.path.exists(pipes_file):
        try:
            with open(pipes_file, 'r') as f:
                pipes = json.load(f)
        except Exception as e:
            st.sidebar.error(f"Failed to load {pipes_file}: {e}")
    else:
        st.sidebar.warning(f"Missing: {pipes_file}")
    
    # Load image
    image_file = config["image_file"]
    if os.path.exists(image_file):
        image = image_file
    else:
        st.sidebar.error(f"Missing: {image_file}")
    
    return valves, pipes, image

# ==================== CORE TOGGLE LOGIC ====================
def update_active_pipes(system_name, valves):
    """
    Update which pipes are active based on which valves are open.
    A pipe is active if ANY valve that controls it is open.
    """
    active = set()
    
    for valve_tag, valve_data in valves.items():
        if st.session_state.valve_states.get(valve_tag, False):  # Valve is OPEN
            connected_pipes = valve_data.get("connected_pipes", [])
            # Add all pipes this valve controls
            for pipe_ref in connected_pipes:
                # Handle both 0-based and 1-based indexing
                if isinstance(pipe_ref, int):
                    # If pipe numbers are 1-based in JSON, convert to 0-based
                    pipe_idx = pipe_ref - 1 if pipe_ref > 0 else pipe_ref
                    if isinstance(pipe_idx, int):
                        active.add(pipe_idx)
    
    # Store per system
    st.session_state.active_pipes = active
    return active

def get_pipe_color(pipe_idx, system_name, valves, pipes):
    """
    Determine pipe color:
    - GREEN: Pipe is controlled by an OPEN valve (in active_pipes set)
    - BLUE: Pipe is a pressure source (but no open valve controls it)
    - GRAY: Inactive
    """
    # Check if this pipe is controlled by any open valve
    if pipe_idx in st.session_state.active_pipes:
        return (0, 255, 0)  # GREEN - valve is open for this pipe
    
    # Check if it's a pressure source
    pressure_sources = SYSTEM_CONFIG[system_name]["pressure_sources"]
    pipe_num = pipe_idx + 1  # Convert to 1-based for comparison
    
    if pipe_num in pressure_sources:
        return (100, 200, 255)  # LIGHT BLUE - pressure source
    
    return (80, 80, 100)  # GRAY - inactive

# ==================== RENDERING ====================
def render_system(valves, pipes, image_path, system_name):
    """Render the P&ID with valve and pipe overlays"""
    # Load or create image
    try:
        img = Image.open(image_path).convert("RGBA")
    except:
        # Create placeholder
        img = Image.new('RGBA', (800, 600), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        draw.text((100, 100), f"{system_name.upper()} SYSTEM", fill="white", size=30)
    
    draw = ImageDraw.Draw(img)
    
    # Update active pipes based on current valve states
    active_pipes = update_active_pipes(system_name, valves)
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        color = get_pipe_color(i, system_name, valves, pipes)
        width = 8 if i in active_pipes else 4
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                  fill=color, width=width)
        
        # Draw pipe number (for debugging)
        mid_x = (pipe["x1"] + pipe["x2"]) // 2
        mid_y = (pipe["y1"] + pipe["y2"]) // 2
        if i in active_pipes:
            draw.text((mid_x, mid_y), str(i+1), fill="white", stroke_fill="black")
    
    # Draw valves
    for tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(tag, False)
        
        # Valve color
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)
        
        # Draw valve circle
        radius = 12 if is_open else 10
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                    fill=valve_color, outline="white", width=2)
        
        # Show connected pipes count inside valve
        connected = valve_data.get("connected_pipes", [])
        if connected:
            draw.text((x-6, y-8), str(len(connected)), 
                     fill="white", stroke_fill="black", stroke_width=1)
        
        # Valve label
        draw.text((x+15, y-10), tag, 
                 fill="white", stroke_fill="black", stroke_width=1)
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
def show_home_page():
    st.title("🏭 Rig Simulation Dashboard")
    st.markdown("### Click a system to control valves and see connected pipes toggle")
    
    # System cards
    cols = st.columns(5)
    systems = [
        ("mixing", "🔧", "Mixing Area"),
        ("supply", "⚡", "Pressure Supply"),
        ("dgs", "🎮", "DGS Simulation"),
        ("return", "🔄", "Pressure Return"),
        ("seal", "🔒", "Separation Seal")
    ]
    
    for idx, (sys_id, icon, name) in enumerate(systems):
        with cols[idx]:
            if st.button(f"{icon}\n\n**{name}**", 
                        use_container_width=True, 
                        key=f"home_{sys_id}",
                        help=f"Open {name} system"):
                st.session_state.current_system = sys_id
                st.rerun()
    
    st.markdown("---")
    
    # Quick system info
    st.subheader("📋 System Overview")
    
    for sys_id, config in SYSTEM_CONFIG.items():
        with st.expander(f"{config['display_name']} System"):
            valves_exist = os.path.exists(config["valves_file"])
            pipes_exist = os.path.exists(config["pipes_file"])
            
            if valves_exist:
                try:
                    with open(config["valves_file"], 'r') as f:
                        valves = json.load(f)
                        valve_count = len(valves)
                        
                        # Count total connected pipes
                        total_connections = 0
                        valve_connections = []
                        for tag, data in valves.items():
                            conn = data.get("connected_pipes", [])
                            total_connections += len(conn)
                            if conn:
                                valve_connections.append(f"{tag}: {len(conn)} pipes")
                        
                        st.write(f"**{valve_count} valves**")
                        st.write(f"**{total_connections} pipe connections**")
                        if valve_connections:
                            st.write("**Valve connections:**")
                            for vc in valve_connections:
                                st.write(f"- {vc}")
                except:
                    st.write("Could not load valve data")
            else:
                st.write("❌ Valve file not found")

# ==================== SYSTEM PAGE ====================
def show_system_page(system_name):
    config = SYSTEM_CONFIG[system_name]
    
    # Load system data
    valves, pipes, image_path = load_system_data(system_name)
    
    # Initialize valve states if not exists
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Update active pipes
    active_pipes = update_active_pipes(system_name, valves)
    
    # Header
    st.title(f"{config['display_name']} System")
    
    # Back button
    if st.button("← Back to Home", key="back_home"):
        st.session_state.current_system = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Main layout
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        st.header("🎛️ Valve Controls")
        st.markdown("Click valves to toggle them ON/OFF")
        
        # Valve toggles - SIMPLIFIED FIXED VERSION
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected = valve_data.get("connected_pipes", [])
            
            # Create toggle button
            if is_open:
                button_text = f"🟢 **{tag}** - OPEN"
                button_help = f"Controls pipes: {connected}"
            else:
                button_text = f"🔴 **{tag}** - CLOSED"
                button_help = f"Controls pipes: {connected}"
            
            if st.button(button_text, 
                        key=f"toggle_{system_name}_{tag}",
                        help=button_help,
                        use_container_width=True):
                # Toggle the valve
                st.session_state.valve_states[tag] = not is_open
                # Immediately update active pipes
                update_active_pipes(system_name, valves)
                st.rerun()
            
            # Show connected pipes below each valve
            if connected:
                pipe_nums = [p+1 if isinstance(p, int) and p >= 0 else p for p in connected]
                st.caption(f"→ Pipes: {pipe_nums}")
        
        st.markdown("---")
        st.header("📊 Live Stats")
        
        # Calculate stats
        open_valves = sum(1 for tag in valves if st.session_state.valve_states.get(tag, False))
        active_pipe_count = len(active_pipes)
        pressure_source_count = len([i for i in range(len(pipes)) 
                                     if (i+1) in config["pressure_sources"]])
        
        st.metric("Open Valves", f"{open_valves}/{len(valves)}")
        st.metric("Active Pipes", active_pipe_count)
        st.metric("Pressure Sources", pressure_source_count)
        st.metric("Total Pipes", len(pipes))
        
        st.markdown("---")
        st.header("⚙️ Quick Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 Close All", use_container_width=True, key="close_all"):
                for tag in valves:
                    st.session_state.valve_states[tag] = False
                update_active_pipes(system_name, valves)
                st.rerun()
        
        with col2:
            if st.button("🟢 Open All", use_container_width=True, key="open_all"):
                for tag in valves:
                    st.session_state.valve_states[tag] = True
                update_active_pipes(system_name, valves)
                st.rerun()
        
        # Test patterns
        st.markdown("---")
        st.header("🌀 Test Patterns")
        
        if st.button("Pattern A: Open First 3", use_container_width=True):
            valve_list = list(valves.keys())
            for i, tag in enumerate(valve_list):
                st.session_state.valve_states[tag] = (i < 3)
            update_active_pipes(system_name, valves)
            st.rerun()
        
        if st.button("Pattern B: Open Alternating", use_container_width=True):
            valve_list = list(valves.keys())
            for i, tag in enumerate(valve_list):
                st.session_state.valve_states[tag] = (i % 2 == 0)
            update_active_pipes(system_name, valves)
            st.rerun()
        
        st.markdown("---")
        st.header("🎯 Legend")
        st.write("🟢 **Green pipe** = Controlled by OPEN valve")
        st.write("🔵 **Blue pipe** = Pressure source")
        st.write("⚫ **Gray pipe** = Inactive")
        st.write("🟢 **Green valve** = OPEN")
        st.write("🔴 **Red valve** = CLOSED")
        st.write("📝 **Number on valve** = How many pipes it controls")
    
    with col_main:
        # Render and display
        if image_path:
            rendered_img = render_system(valves, pipes, image_path, system_name)
            st.image(rendered_img, use_container_width=True,
                    caption=f"{config['display_name']} - Green pipes = controlled by open valves")
        else:
            st.error("⚠️ P&ID image not found")
            st.info(f"Expected at: {config['image_file']}")
        
        # Active pipes display
        st.markdown("---")
        st.subheader("🔗 Active Pipe Connections")
        
        if active_pipes:
            st.success(f"✅ **{len(active_pipes)} pipes are active** (controlled by open valves)")
            
            # Show which valves control which active pipes
            for valve_tag, valve_data in valves.items():
                if st.session_state.valve_states.get(valve_tag, False):
                    connected = valve_data.get("connected_pipes", [])
                    active_from_valve = [p for p in connected if p in active_pipes]
                    if active_from_valve:
                        # Convert to 1-based for display
                        pipe_nums = [p+1 if isinstance(p, int) and p >= 0 else p for p in active_from_valve]
                        st.write(f"🟢 **{valve_tag}** → Pipes: {pipe_nums}")
        else:
            st.info("ℹ️ No pipes are active. Open valves to activate their connected pipes.")
        
        # Pipe details table
        st.markdown("---")
        st.subheader("📋 Pipe Status")
        
        pipe_data = []
        for i in range(len(pipes)):
            pipe_num = i + 1
            is_active = i in active_pipes
            is_pressure = pipe_num in config["pressure_sources"]
            
            # Find which valves control this pipe
            controlling_valves = []
            for valve_tag, valve_data in valves.items():
                connected = valve_data.get("connected_pipes", [])
                if i in connected:
                    controlling_valves.append(valve_tag)
            
            status = "🟢 ACTIVE" if is_active else "⚫ INACTIVE"
            if is_pressure:
                status = "🔵 PRESSURE"
            
            pipe_data.append({
                "Pipe": pipe_num,
                "Status": status,
                "Controlled by": ", ".join(controlling_valves) if controlling_valves else "None"
            })
        
        # Display pipe table
        for pipe in pipe_data:
            cols = st.columns([1, 1, 2])
            cols[0].metric("", f"Pipe {pipe['Pipe']}")
            cols[1].write(pipe['Status'])
            cols[2].write(pipe['Controlled by'])

# ==================== MAIN APP ====================
# Sidebar navigation
st.sidebar.title("🏭 Navigation")

# System selector
st.sidebar.header("📁 Select System")
for sys_id, config in SYSTEM_CONFIG.items():
    if st.sidebar.button(config["display_name"], 
                        key=f"nav_{sys_id}",
                        use_container_width=True):
        st.session_state.current_system = sys_id
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("ℹ️ How It Works")
st.sidebar.info("""
**Valve Toggle Logic:**
1. Each valve in the JSON has a `"connected_pipes"` list
2. When you OPEN a valve → ALL pipes in its list turn GREEN
3. When you CLOSE a valve → Those pipes turn GRAY
4. Multiple valves can control the same pipe
""")

st.sidebar.markdown("---")
st.sidebar.header("🔧 JSON Format")
st.sidebar.code("""
{
  "V-101": {
    "x": 100,
    "y": 200,
    "connected_pipes": [1, 2, 3]  // Pipe numbers (1-based)
  }
}
""")

# Show appropriate page
if st.session_state.current_system == "home":
    show_home_page()
else:
    show_system_page(st.session_state.current_system)

# Footer
st.markdown("---")
st.caption("🏭 Rig Simulation v2.1 | Valve-to-Pipe Toggle System | Click valves to see connected pipes turn GREEN")
