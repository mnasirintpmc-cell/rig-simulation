import streamlit as st
import importlib.util
import os

st.set_page_config(layout="wide", page_title="Rig Simulation Dashboard")

# ---- Load mixing page manually (file contains &) ----
def load_page(path):
    spec = importlib.util.spec_from_file_location("mixing_page", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MIXING_FILE = "page/app_mixing_p&id.py"

if not os.path.exists(MIXING_FILE):
    st.error(f"Mixing page file not found: {MIXING_FILE}")
    st.stop()

app_mixing = load_page(MIXING_FILE)

# ---- Sidebar Navigation ----
st.sidebar.title("Rig Simulation Menu")

page = st.sidebar.radio(
    "Select System:",
    ["🏭 Home", "🔀 Mixing Area"],
    index=0
)

# ---- Main Pages ----
if page == "🏭 Home":
    st.title("Rig Simulation Dashboard")
    st.write("Welcome to the Rig Simulation System.")
    st.write("Select **Mixing Area** from the sidebar to begin.")

elif page == "🔀 Mixing Area":
    app_mixing.run()
