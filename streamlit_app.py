# streamlit_app.py - COMPLETE 5-SYSTEM RIG SIMULATION
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
if 'system_pressure_sources' not in st.session_state:
    st.session_state.system_pressure_sources = {}

# ==================== SYSTEM CONFIGURATION ====================
SYSTEM_CONFIG = {
    "mixing": {
        "display_name": "Mixing Area",
        "valves_file": "data/valves_mixing.json",
        "pipes_file": "data/pipes_mixing.json", 
        "image_file": "assets/p&id_mixing.png",
        "pressure_sources": [1, 5],
        "default_valves": ["V-101", "V-102", "V-103", "V-104", "V-105"]
    },
    "supply": {
        "display_name": "Pressure Supply",
        "valves_file": "data/valves_pressure_in.json",
        "pipes_file": "data/pipes_pressure_in.json",
        "image_file": "assets/p&id_pressure_in.png",
        "pressure_sources": [1, 3, 7],
        "default_valves": ["V-201", "V-202", "V-203", "V-204", "V-205"]
    },
    "dgs": {
        "display_name": "DGS Simulation",
        "valves_file": "data/valves_dgs.json",
        "pipes_file": "data/pipes_dgs.json",
        "image_file": "assets/p&id_dgs.png",
        "pressure_sources": [1, 6, 11],
        "default_valves": ["V-301", "V-302", "V-303", "V-304", "V-305"]
    },
    "return": {
        "display_name": "Pressure Return",
        "valves_file": "data/valves_pressure_return.json",
        "pipes_file": "data/pipes_pressure_return.json",
        "image_file": "assets/p&id_pressure_return.png",
        "pressure_sources": [2, 8],
        "default_valves": ["V-401", "V-402", "V-403", "V-404", "V-405"]
    },
    "seal": {
        "display_name": "Separation Seal",
        "valves_file": "data/valves_separation_seal.json",
        "pipes_file": "data/pipes_separation_seal.json",
        "image_file": "assets/p&id_separation_seal.png",
        "pressure_sources": [1, 4, 9],
        "default_valves": ["V-501", "V-502", "V-503", "V-504", "V-505"]
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
        except:
            st.sidebar.error(f"Failed to load {valves_file}")
    else:
        st.sidebar.warning(f"Missing: {valves_file}")
        # Create sample valves
        for v in config["default_valves"]:
            valves[v] = {"x": 100, "y": 100, "connected_pipes": [1, 2, 3]}
    
    # Load pipes
    pipes_file = config["pipes_file"]
    if os.path.exists(pipes_file):
        try:
            with open(pipes_file, 'r') as f:
                pipes = json.load(f)
        except:
            st.sidebar.error(f"Failed to load {pipes_file}")
    else:
        st.sidebar.warning(f"Missing: {pipes_file}")
        # Create sample pipes
        pipes = [
            {"x1": 50, "y1": 50, "x2": 150, "y2": 50},
            {"x1": 150, "y1": 50, "x2": 150, "y2": 150},
            {"x1": 150, "y1": 150, "x2": 250, "y2": 150}
        ]
    
    # Load image
    image_file = config["image_file"]
    if os.path.exists(image_file):
        image = image_file
    else:
        st.sidebar.error(f"Missing: {image_file}")
    
    return valves, pipes, image

# ==================== PRESSURE & FLOW LOGIC ====================
def get_pipe_status(pipe_idx, valves, valve_states, pressure_sources):
    """
    Determine if a pipe is:
    - FLOWING (green): Connected to an open valve AND has pressure
    - PRESSURIZED (blue): Is a pressure source or connected to one
    - INACTIVE (gray): Neither
    """
    pipe_num = pipe_idx + 1
    
    # Check if pipe is a pressure source
    if pipe_num in pressure_sources:
        # Check if any valve controlling this pipe is open
        for valve_tag, valve_data in valves.items():
            if valve_states.get(valve_tag, False):
                connected = valve_data.get("connected_pipes", [])
                if pipe_num in connected or pipe_idx in connected:
                    return "flowing"  # Has pressure AND valve open
        return "pressurized"  # Has pressure but no valve open
    
    # Check if pipe is connected to an open valve
    for valve_tag, valve_data in valves.items():
        if valve_states.get(valve_tag, False):
            connected = valve_data.get("connected_pipes", [])
            if pipe_num in connected or pipe_idx in connected:
                # Check if this pipe gets pressure from upstream
                # For simplicity, if valve is open and pipe is connected, it flows
                return "flowing"
    
    return "inactive"

def get_pipe_color(status):
    """Return RGB color based on pipe status"""
    colors = {
        "flowing": (0, 255, 0),      # Green
        "pressurized": (100, 200, 255),  # Light Blue
        "inactive": (80, 80, 100)    # Dark Gray
    }
    return colors.get(status, (80, 80, 100))

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
    pressure_sources = SYSTEM_CONFIG[system_name]["pressure_sources"]
    
    # Draw pipes
    for i, pipe in enumerate(pipes):
        status = get_pipe_status(i, valves, st.session_state.valve_states, pressure_sources)
        color = get_pipe_color(status)
        width = 6 if status == "flowing" else 4
        draw.line([(pipe["x1"], pipe["y1"]), (pipe["x2"], pipe["y2"])], 
                  fill=color, width=width)
    
    # Draw valves
    for tag, valve_data in valves.items():
        x, y = valve_data["x"], valve_data["y"]
        is_open = st.session_state.valve_states.get(tag, False)
        
        # Valve color
        valve_color = (0, 255, 0) if is_open else (255, 0, 0)
        
        # Draw valve circle
        radius = 10
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                    fill=valve_color, outline="white", width=2)
        
        # Show connected pipes count
        connected = valve_data.get("connected_pipes", [])
        if connected:
            draw.text((x-5, y-8), str(len(connected)), 
                     fill="white", stroke_fill="black", stroke_width=1)
        
        # Valve label
        draw.text((x+15, y-10), tag, 
                 fill="white", stroke_fill="black", stroke_width=1)
    
    return img.convert("RGB")

# ==================== HOME PAGE ====================
def show_home_page():
    st.title("🏭 Rig Simulation Dashboard")
    st.markdown("### Select a system to visualize and control valves")
    
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
                        key=f"home_{sys_id}"):
                st.session_state.current_system = sys_id
                st.rerun()
    
    st.markdown("---")
    
    # System status table
    st.subheader("📊 System Status")
    
    status_data = []
    for sys_id, config in SYSTEM_CONFIG.items():
        # Check file existence
        valves_exist = os.path.exists(config["valves_file"])
        pipes_exist = os.path.exists(config["pipes_file"])
        image_exist = os.path.exists(config["image_file"])
        
        status = "✅ Ready" if all([valves_exist, pipes_exist, image_exist]) else "⚠️ Missing Files"
        
        # Count valves in file
        valve_count = 0
        if valves_exist:
            try:
                with open(config["valves_file"], 'r') as f:
                    valves = json.load(f)
                    valve_count = len(valves)
            except:
                valve_count = 0
        
        status_data.append({
            "System": config["display_name"],
            "Status": status,
            "Valves": valve_count,
            "Files": f"{'✅' if valves_exist else '❌'} Valves | {'✅' if pipes_exist else '❌'} Pipes | {'✅' if image_exist else '❌'} Image"
        })
    
    # Display as metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    for idx, (sys_id, config) in enumerate(SYSTEM_CONFIG.items()):
        col = [col1, col2, col3, col4, col5][idx]
        with col:
            valves_exist = os.path.exists(config["valves_file"])
            if valves_exist:
                try:
                    with open(config["valves_file"], 'r') as f:
                        valves = json.load(f)
                        valve_count = len(valves)
                        col.metric(config["display_name"], f"{valve_count} valves")
                except:
                    col.metric(config["display_name"], "Error")
            else:
                col.metric(config["display_name"], "No file")

# ==================== SYSTEM PAGE ====================
def show_system_page(system_name):
    config = SYSTEM_CONFIG[system_name]
    
    # Load system data
    valves, pipes, image_path = load_system_data(system_name)
    
    # Initialize valve states
    for tag in valves:
        if tag not in st.session_state.valve_states:
            st.session_state.valve_states[tag] = False
    
    # Header with back button
    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.title(f"{config['display_name']} System")
    with col_back:
        if st.button("🏠 Back to Home"):
            st.session_state.current_system = "home"
            st.rerun()
    
    # Main layout
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        st.header("🎛️ Valve Controls")
        
        # Valve toggles
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected_pipes = valve_data.get("connected_pipes", [])
            
            # Button label
            status_icon = "🟢" if is_open else "🔴"
            pipe_info = f" → Pipes: {connected_pipes}" if connected_pipes else ""
            button_label = f"{status_icon} {tag}{pipe_info}"
            
            if st.button(button_label, key=f"valve_{tag}", use_container_width=True):
                st.session_state.valve_states[tag] = not is_open
                st.rerun()
        
        st.markdown("---")
        st.header("📊 System Stats")
        
        # Calculate stats
        open_valves = sum(1 for tag in valves if st.session_state.valve_states.get(tag, False))
        total_valves = len(valves)
        
        flowing_pipes = 0
        pressurized_pipes = 0
        for i in range(len(pipes)):
            status = get_pipe_status(i, valves, st.session_state.valve_states, config["pressure_sources"])
            if status == "flowing":
                flowing_pipes += 1
            elif status == "pressurized":
                pressurized_pipes += 1
        
        st.metric("Open Valves", f"{open_valves}/{total_valves}")
        st.metric("Flowing Pipes", flowing_pipes)
        st.metric("Pressurized Pipes", pressurized_pipes)
        st.metric("Total Pipes", len(pipes))
        
        # Control buttons
        st.markdown("---")
        st.header("⚙️ Controls")
        
        col_reset, col_test = st.columns(2)
        with col_reset:
            if st.button("🔴 Close All", use_container_width=True):
                for tag in valves:
                    st.session_state.valve_states[tag] = False
                st.rerun()
        
        with col_test:
            if st.button("🟢 Open All", use_container_width=True):
                for tag in valves:
                    st.session_state.valve_states[tag] = True
                st.rerun()
        
        # Pressure sources info
        st.markdown("---")
        st.header("💡 Info")
        st.write(f"**Pressure Sources:** Pipes {config['pressure_sources']}")
        st.write("**Legend:**")
        st.write("🟢 Green pipe = Flowing (valve open + pressure)")
        st.write("🔵 Blue pipe = Pressurized (no valve open)")
        st.write("⚫ Gray pipe = Inactive")
        st.write("🟢 Green valve = Open")
        st.write("🔴 Red valve = Closed")
        
        # File info
        st.markdown("---")
        st.header("📁 Files")
        st.write(f"**Valves:** {os.path.basename(config['valves_file'])}")
        st.write(f"**Pipes:** {os.path.basename(config['pipes_file'])}")
        st.write(f"**Image:** {os.path.basename(config['image_file'])}")
    
    with col_main:
        # Render and display
        if image_path:
            rendered_img = render_system(valves, pipes, image_path, system_name)
            st.image(rendered_img, use_container_width=True,
                    caption=f"{config['display_name']} - Real-time Valve Control")
        else:
            st.error("⚠️ P&ID image not found")
            st.info(f"Expected at: {config['image_file']}")
        
        # Valve connections table
        st.markdown("---")
        st.subheader("🔗 Valve Connections")
        
        connection_data = []
        for tag, valve_data in valves.items():
            is_open = st.session_state.valve_states.get(tag, False)
            connected = valve_data.get("connected_pipes", [])
            
            # Count active pipes from this valve
            active_from_this = 0
            if is_open:
                for pipe_ref in connected:
                    pipe_idx = pipe_ref - 1 if isinstance(pipe_ref, int) and pipe_ref > 0 else pipe_ref
                    if isinstance(pipe_idx, int) and 0 <= pipe_idx < len(pipes):
                        status = get_pipe_status(pipe_idx, valves, st.session_state.valve_states, config["pressure_sources"])
                        if status == "flowing":
                            active_from_this += 1
            
            connection_data.append({
                "Valve": tag,
                "Status": "🟢 OPEN" if is_open else "🔴 CLOSED",
                "Connected Pipes": str(connected),
                "Active Pipes": active_from_this
            })
        
        # Display as table
        for conn in connection_data:
            cols = st.columns([1, 1, 2, 1])
            cols[0].write(f"**{conn['Valve']}**")
            cols[1].write(conn['Status'])
            cols[2].write(conn['Connected Pipes'])
            cols[3].write(f"🔧 {conn['Active Pipes']}")
        
        # Quick actions
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌀 Test Flow Pattern 1", use_container_width=True):
                # Open first 2 valves
                valve_list = list(valves.keys())
                for i, tag in enumerate(valve_list):
                    st.session_state.valve_states[tag] = (i < 2)
                st.rerun()
        
        with col2:
            if st.button("🌀 Test Flow Pattern 2", use_container_width=True):
                # Open every other valve
                valve_list = list(valves.keys())
                for i, tag in enumerate(valve_list):
                    st.session_state.valve_states[tag] = (i % 2 == 0)
                st.rerun()
        
        with col3:
            if st.button("📊 Export Status", use_container_width=True):
                # Create status report
                report = {
                    "system": system_name,
                    "timestamp": st.session_state.get("_last_update", "N/A"),
                    "valve_states": st.session_state.valve_states,
                    "stats": {
                        "open_valves": open_valves,
                        "flowing_pipes": flowing_pipes,
                        "pressurized_pipes": pressurized_pipes
                    }
                }
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json.dumps(report, indent=2),
                    file_name=f"{system_name}_status.json",
                    mime="application/json"
                )

# ==================== MAIN APP ====================
# Navigation
st.sidebar.title("🏭 Rig Simulation")

# System selector in sidebar
st.sidebar.header("📁 Systems")
for sys_id, config in SYSTEM_CONFIG.items():
    if st.sidebar.button(config["display_name"], key=f"sidebar_{sys_id}", use_container_width=True):
        st.session_state.current_system = sys_id
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("ℹ️ About")
st.sidebar.info(
    "This simulator shows real-time pipe flow based on valve states. "
    "Toggle valves to control which pipes are active."
)

# Show appropriate page
if st.session_state.current_system == "home":
    show_home_page()
else:
    show_system_page(st.session_state.current_system)

# Footer
st.markdown("---")
st.caption("🏭 Rig Simulation v2.0 | Valve-to-Pipe Toggle System | All 5 Systems Integrated")
