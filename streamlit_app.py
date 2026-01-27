import streamlit as st
import pandas as pd
import time

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Rig Simulation Platform",
    page_icon="🏭",
    layout="wide"
)

# ===============================
# SESSION STATE
# ===============================
if "current_system" not in st.session_state:
    st.session_state.current_system = "home"

if "df" not in st.session_state:
    st.session_state.df = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()

# ===============================
# SYSTEM DEFINITIONS
# ===============================
SYSTEMS = {
    "mixing": "🔧 Mixing",
    "supply": "⚡ Supply",
    "dgs": "🎮 DGS",
    "return": "🔄 Return",
    "seal": "🔒 Seal",
}

# ===============================
# CSV → LOGIC MAP
# ===============================
PIPE_MAP = {
    "CELL_PRESSURE": "TST_CellPresDemand",
    "INTER_PRESSURE": "TST_InterPresDemand",
    "BP_DE": "TST_InterBPDemand_DE",
    "BP_NDE": "TST_InterBPDemand_NDE",
    "GAS_INJECTION": "TST_GasInjectionDemand",
}

# ===============================
# FUNCTIONS
# ===============================
def load_csv(upload):
    return pd.read_csv(upload, sep=";")

def get_active_pipes(row):
    return {k: float(row[v]) > 0 for k, v in PIPE_MAP.items()}

def advance_step():
    df = st.session_state.df
    step = st.session_state.step
    duration = float(df.iloc[step]["TST_StepDuration"])
    elapsed = time.time() - st.session_state.last_tick

    if elapsed >= max(duration, 0.1):
        st.session_state.step += 1
        st.session_state.last_tick = time.time()
        if st.session_state.step >= len(df):
            st.session_state.step = len(df) - 1
            st.session_state.playing = False

def rig_box(title, active, value):
    if active:
        bg = "#198754"
        glow = "box-shadow:0 0 12px rgba(25,135,84,.8);"
    else:
        bg = "#343a40"
        glow = ""

    st.markdown(
        f"""
        <div style="
            background:{bg};
            color:white;
            padding:16px;
            border-radius:12px;
            text-align:center;
            font-weight:bold;
            {glow}
        ">
            {title}<br>
            Demand: {value}
        </div>
        """,
        unsafe_allow_html=True
    )

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("🏭 Rig Control")

    if st.button("🏠 Home"):
        st.session_state.current_system = "home"

    st.markdown("---")

    csv_file = st.file_uploader("Upload Test CSV", type=["csv"])
    if csv_file:
        st.session_state.df = load_csv(csv_file)
        st.session_state.step = 0
        st.session_state.playing = False
        st.session_state.last_tick = time.time()
        st.success("CSV Loaded")

    if st.session_state.df is not None:
        st.markdown("---")
        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause"):
            st.session_state.playing = not st.session_state.playing
            st.session_state.last_tick = time.time()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏮ Prev"):
                st.session_state.step = max(0, st.session_state.step - 1)
                st.session_state.last_tick = time.time()
        with col2:
            if st.button("⏭ Next"):
                st.session_state.step = min(
                    len(st.session_state.df) - 1,
                    st.session_state.step + 1
                )
                st.session_state.last_tick = time.time()

# ===============================
# HOME PAGE
# ===============================
if st.session_state.current_system == "home":
    st.title("🏭 Rig Simulation – Home")

    cols = st.columns(len(SYSTEMS))
    for i, (sys_id, name) in enumerate(SYSTEMS.items()):
        with cols[i]:
            if st.button(name, use_container_width=True):
                st.session_state.current_system = sys_id

    st.markdown("---")
    st.info("Select a system. CSV simulation drives all systems when active.")
    st.stop()

# ===============================
# SYSTEM PAGE
# ===============================
system = st.session_state.current_system
st.title(f"{SYSTEMS[system]} System")

if st.session_state.df is None:
    st.warning("Upload CSV to activate simulation.")
    st.stop()

# Auto-play
if st.session_state.playing:
    advance_step()
    time.sleep(0.05)
    st.rerun()

row = st.session_state.df.iloc[st.session_state.step]
active = get_active_pipes(row)

# ===============================
# STATUS
# ===============================
col_a, col_b = st.columns([2, 3])

with col_a:
    st.subheader("🧠 Test Status")
    st.write(f"**Gas:** {row['TST_GasType']}")
    st.write(f"**Mode:** {int(row['TST_TestMode'])}")
    st.metric("Step Duration (s)", float(row["TST_StepDuration"]))

with col_b:
    st.subheader("📊 Demands")
    st.dataframe(
        row[list(PIPE_MAP.values())].to_frame("Value"),
        use_container_width=True
    )

# ===============================
# LOGICAL VIEW (ACTIVE SYSTEM)
# ===============================
st.markdown("---")
st.subheader("🧩 System Activity")

c1, c2, c3 = st.columns(3)
with c1:
    rig_box("CELL PRESSURE", active["CELL_PRESSURE"], row["TST_CellPresDemand"])
with c2:
    rig_box("INTER PRESSURE", active["INTER_PRESSURE"], row["TST_InterPresDemand"])
with c3:
    rig_box("GAS INJECTION", active["GAS_INJECTION"], row["TST_GasInjectionDemand"])

c4, c5 = st.columns(2)
with c4:
    rig_box("BP DE", active["BP_DE"], row["TST_InterBPDemand_DE"])
with c5:
    rig_box("BP NDE", active["BP_NDE"], row["TST_InterBPDemand_NDE"])

# ===============================
# RAW DATA
# ===============================
with st.expander("🔍 Raw CSV Row"):
    st.write(row)
