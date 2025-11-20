import os
import streamlit as st

st.set_page_config(layout="wide")
st.title("🔍 Compare System Files")

st.subheader("Checking ALL System Files:")

systems = ["mixing", "supply", "return", "seal", "dgs"]

for system in systems:
    st.markdown(f"### 🔧 {system.upper()} System")
    
    # Check valves
    valves_paths = [
        f"data/valves_{system}.json",
        f"data/valves_{system}_p&id.json", 
        f"valves_{system}.json"
    ]
    
    valves_found = None
    for path in valves_paths:
        if os.path.exists(path):
            valves_found = path
            break
    
    # Check pipes
    pipes_paths = [
        f"data/pipes_{system}.json",
        f"data/pipes_{system}_p&id.json",
        f"pipes_{system}.json"
    ]
    
    pipes_found = None
    for path in pipes_paths:
        if os.path.exists(path):
            pipes_found = path
            break
    
    # Check PNG
    png_paths = [
        f"assets/p&id_{system}.png",
        f"assets/p&id_{system}_p&id.png",
        f"assets/{system}.png",
        f"p&id_{system}.png"
    ]
    
    png_found = None
    for path in png_paths:
        if os.path.exists(path):
            png_found = path
            break
    
    # Display results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if valves_found:
            st.success(f"✅ Valves: {valves_found}")
        else:
            st.error("❌ Valves: NOT FOUND")
    
    with col2:
        if pipes_found:
            st.success(f"✅ Pipes: {pipes_found}")
        else:
            st.error("❌ Pipes: NOT FOUND")
    
    with col3:
        if png_found:
            st.success(f"✅ PNG: {png_found}")
        else:
            st.error("❌ PNG: NOT FOUND")
    
    # Show file sizes if found
    if valves_found:
        size = os.path.getsize(valves_found)
        st.write(f"Valves file size: {size} bytes")
    
    if pipes_found:
        size = os.path.getsize(pipes_found)
        st.write(f"Pipes file size: {size} bytes")
    
    if png_found:
        size = os.path.getsize(png_found)
        st.write(f"PNG file size: {size} bytes")
    
    st.markdown("---")
