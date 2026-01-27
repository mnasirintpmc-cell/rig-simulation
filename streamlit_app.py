# streamlit_app.py
# CSV-DRIVEN RIG SIMULATION (NO P&ID REQUIRED)

import streamlit as st
import pandas as pd
import time

# =========================
# PAGE CONFIG
# =========================
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
# PIPE ↔ CSV MAPPING
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
    return pd.read_csv(upload, sep=";")


def get_active_pipes(row):
    states = {}
    for pipe, col in PIPE_MAP.items():
        states[pipe] = float(row[col]) > 0
    return states


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
        color = "#198754"
        glow = "box-shadow:0 0 12px rgba(25,135,84,0.8);"
        status = "ACTIVE"
    else:
        color = "#343a40"
        glow = ""
        status = "inactive"

    st.markdown(
        f"""
        <div style="
            background:{color};
            color:white;
            padding:18px;
            border-radius:12px;
            text-align:center;
            font-weight:bold;
            {glow}
        ">
            {title}<br>
            <small>{status}</small><br>
            Demand: {value}
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("📂 Test Sequence")

    csv_file = st.file_uploader(
        "Upload CSV (semicolon separated)",
        type=["csv"]
    )

    if csv_file:
        st.session_state.df = load_csv(csv_file)
        st.session_state.step = 0
        st.session_state.last_tick = time.time()
        st.session_state.playing = False
        st.success("CSV loaded successfully")

    st.markdown("---")

    if st.session_state.df is not None:
        st.subheader("Playback")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⏮ Prev"):
                st.session_state.step = max(0, st.session_state.step - 1)
                st.session_state.last_tick = time.time()
        with c2:
            if st.button("⏭ Next"):
                st.session_state.step = min(
                    len(st.session_state.df) - 1,
                    st.session_state.step + 1
                )
                st.session_state.last_tick = time.time()

        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause"):
            st.session_state.playing = not st.session_state.playing
            st.session_state.last_tick = time.time()

        st.metric(
            "Step",
            f"{st.session_state.step + 1} / {len(st.session_state.df)}"
        )

# =========================
# MAIN VIEW
# =========================
st.title("🏭 Rig Test Sequence Simulation")

if st.session_state.df is None:
    st.info("Upload your CSV test sequence to start the simulation.")
    st.stop()

# Auto-play
if st.session_state.playing:
    advance_step()
    time.sleep(0.05)
    st.rerun()

row = st.session_state.df.iloc[st.session_state.step]
active = get_active_pipes(row)

# =========================
# STATUS + VALUES
# =========================
col_a, col_b = st.columns([2, 3])

with col_a:
    st.subheader("🧠 Test Status")
    st.write(f"**Gas Type:** {row['TST_GasType']}")
    st.write(f"**Test Mode:** {int(row['TST_TestMode'])}")
    st.write(f"**Measurement Req:** {int(row['TST_MeasurementReq'])}")
    st.write(f"**Torque Check:** {int(row['TST_TorqueCheck'])}")
    st.metric("Step Duration (s)", float(row["TST_StepDuration"]))

with col_b:
    st.subheader("📊 Demand Values")
    cols = list(PIPE_MAP.values()) + ["TST_SpeedDem", "TST_TempDemand"]
    st.dataframe(row[cols].to_frame("Value"), use_container_width=True)

# =========================
# LOGICAL RIG VIEW
# =========================
st.markdown("---")
st.subheader("🧩 Logical Rig Simulation")

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

# =========================
# RAW DATA (ENGINEERING VIEW)
# =========================
with st.expander("🔍 Raw CSV Row"):
    st.write(row)
