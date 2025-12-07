# main.py
import streamlit as st
from utils import find_file, load_json, CSVPlayback, SimplePIController
import os


st.set_page_config(page_title="Rig Multi-P&ID Simulation", layout="wide")
st.title("Rig Multi-P&ID Simulation")


# Shared session state
if "valve_states" not in st.session_state:
st.session_state.valve_states = {}
if "playback" not in st.session_state:
st.session_state.playback = None
if "controller" not in st.session_state:
st.session_state.controller = SimplePIController(kp=0.05, ki=0.01)


# --- CSV playback controls ---
with st.sidebar:
st.header("Playback / Test Profile")
uploaded = st.file_uploader("Upload CSV (semicolon-separated)", type=["csv"])
sample_files = ["data/test_profile.csv"]
sample_choice = st.selectbox("Or choose sample", [None] + sample_files)


path = None
if uploaded is not None:
tmp = "data/_uploaded_profile.csv"
with open(tmp, "wb") as f:
f.write(uploaded.getbuffer())
path = tmp
elif sample_choice:
path = sample_choice


if path:
if st.button("Load profile"):
st.session_state.playback = CSVPlayback(path, sep=';')
st.success("Loaded playback")


if st.session_state.playback:
if st.button("Reset playback"):
st.session_state.playback.reset()


if st.button("Step once"):
row = st.session_state.playback.step()
st.write(row)


speed = st.slider("Playback speed (steps/sec)", 1, 10, 2)
st.session_state.playback_speed = speed


st.markdown("---")
st.markdown("Choose a system from the top-right Streamlit Pages (or use the navigation in your existing layout).")
