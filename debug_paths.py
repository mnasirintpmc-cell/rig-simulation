import os
import streamlit as st

st.set_page_config(layout="wide")
st.title("🔍 Debug File Paths")

st.subheader("Current Directory Structure")
st.write("Working directory:", os.getcwd())
st.write("All files:", os.listdir("."))

st.subheader("Assets Folder Contents")
if os.path.exists("assets"):
    st.success("✅ assets folder exists")
    asset_files = os.listdir("assets")
    for file in asset_files:
        st.write(f"- {file}")
else:
    st.error("❌ assets folder not found")

st.subheader("Data Folder Contents")  
if os.path.exists("data"):
    st.success("✅ data folder exists")
    data_files = os.listdir("data")
    for file in data_files:
        st.write(f"- {file}")
else:
    st.error("❌ data folder not found")

st.subheader("Test Specific Paths")
test_paths = [
    "assets/p&id_mixing.png",
    "../assets/p&id_mixing.png", 
    "./assets/p&id_mixing.png",
    "p&id_mixing.png"
]

for path in test_paths:
    exists = os.path.exists(path)
    status = "✅ EXISTS" if exists else "❌ MISSING"
    st.write(f"{status}: {path}")
