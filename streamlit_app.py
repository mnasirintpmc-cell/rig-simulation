# streamlit_app.py
# CSV-DRIVEN RIG SIMULATION (TEST SEQUENCE PLAYER)

import streamlit as st
import pandas as pd
import time

st.set_page_config(
    page_title="Rig Test Sequence Simulation",
    page_icon="🏭",
    layout="wide"
)

# =========================
# SESSION STATE
# =========================
if "df" not in st.session_state:
    st.session_state.df = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()

# =========================
# PIPE MAPPING (LOGICAL)
# =========================
PIPE_MAP = {
    "CELL_PRESSURE": "TST_CellPresDemand",
    "INTER_PRESSURE": "TST_InterPresDemand",
    "BP_DE": "TST_InterBPDemand_DE",
    "BP_NDE": "TST_InterBPDemand_NDE",
    "GAS_INJECTION": "TST_GasInjectionDemand",
}

# =========================
# FUNCTIONS
# =========================
def load_csv(upload):
    df = pd.read_csv(upload, sep=";")
    return df


def get_active_pipes(row):
    active = {}
    for pipe, col in PIPE_MAP.items():
        val = float(row[col])
        active[pipe] = val > 0
    return active


def advance_step():
    if st.session_state.df is None:
        return

    now = time.time()
    elapsed = now - st.session_state.last_tick

    step_duration = float(
        st.session_state.df.iloc[st.session_state.step]["TST_StepDuration"]
    )

    if elapsed >= step_duration:
        st.session_state.step += 1
        st.session_state.last_tick = now

        if st.session_state.step >= len(st.session_state.df):
            st.session_state.step = len(st.session_state.df) - 1
            st.session_state.playing = False


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("📂 Test Sequence")

    csv_file = st.file_uploader(
        "Upload Test CSV",
        type=["csv"]
    )

    if csv_file:
        st.session_state.df = load_csv(csv_file)
        st.session_state.step = 0
        st.session_state.last_tick = time.time()
        st.success("CSV loaded")

    st.markdown("---")

    if st.session_state.df is not None:
        st.write("### Playback Control")

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

        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause"):
            st.session_state.playing = not st.session_state.playing
            st.session_state.last_tick = time.time()

        st.markdown("---")
        st.metric("Step", f"{st.session_state.step + 1} / {len(st.session_state.df)}")

# =========================
# MAIN AREA
# =========================
st.title("🏭 Rig Test Sequence Simulation")

if st.session_state.df is None:
    st.info("Upload a CSV test sequence to begin.")
    st.stop()

# Auto-play logic
if st.session_state.playing:
    advance_step()
    time.sleep(0.05)
    st.rerun()

row = st.session_state.df.iloc[st.session_state.step]
active_pipes = get_active_pipes(row)

# =========================
# STATUS DISPLAY
# =========================
col_status, col_values = st.columns([2, 3])

with col_status:
    st.subheader("🧠 Test Status")

    st.write(f"**Gas Type:** {row['TST_GasType']}")
    st.write(f"**Test Mode:** {int(row['TST_TestMode'])}")
    st.write(f"**Measurement Req:** {int(row['TST_MeasurementReq'])}")
    st.write(f"**Torque Check:** {int(row['TST_TorqueCheck'])}")

    st.markdown("---")
    st.write("### Active Pipes")

    for pipe, active in active_pipes.items():
        if active:
            st.success(f"{pipe} → ACTIVE")
        else:
            st.write(f"{pipe} → inactive")

with col_values:
    st.subheader("📊 Demand Values")

    demand_cols = list(PIPE_MAP.values()) + [
        "TST_SpeedDem",
        "TST_TempDemand"
    ]

    demand_df = row[demand_cols].to_frame(name="Value")
    st.dataframe(demand_df, use_container_width=True)

# =========================
# TIMING
# =========================
st.markdown("---")
st.subheader("⏱ Step Timing")

st.metric(
    "Step Duration (s)",
    float(row["TST_StepDuration"])
)

# =========================
# RAW VIEW (DEBUG / ENGINEERING)
# =========================
with st.expander("🔍 Raw Step Data"):
    st.write(row)
