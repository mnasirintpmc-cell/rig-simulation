import os
import streamlit as st

st.set_page_config(layout="wide")
st.title("🔍 PNG File Location Debug")

st.subheader("Current Directory:")
st.write(os.getcwd())

st.subheader("All Files/Folders:")
for item in os.listdir("."):
    st.write(f"- {item}")

st.subheader("Assets Folder Contents:")
if os.path.exists("assets"):
    st.success("✅ assets/ folder exists")
    for file in os.listdir("assets"):
        st.write(f"- {file}")
else:
    st.error("❌ assets/ folder not found!")

st.subheader("Testing P&ID PNG Files:")
png_files_to_test = [
    "p&id_mixing.png",
    "p&id_pressure_in.png", 
    "p&id_dgs.png",
    "p&id_pressure_return.png",
    "p&id_seperation_seal.png",
    "assets/p&id_mixing.png",
    "assets/p&id_pressure_in.png",
    "assets/p&id_dgs.png", 
    "assets/p&id_pressure_return.png",
    "assets/p&id_seperation_seal.png"
]

for png_file in png_files_to_test:
    exists = os.path.exists(png_file)
    status = "✅ EXISTS" if exists else "❌ MISSING"
    st.write(f"{status}: {png_file}")
