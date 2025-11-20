import os
import streamlit as st

st.set_page_config(layout="wide", page_title="Debug Structure")
st.title("🔍 Complete Directory Structure Analysis")

# Get current working directory
current_dir = os.getcwd()
st.subheader(f"📁 Current Working Directory: `{current_dir}`")

# List all files and folders recursively
st.subheader("📊 Complete File Structure")

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 2 * level
        st.code(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            st.code(f"{subindent}{file}")

list_files(current_dir)

# Check for specific important files
st.subheader("🔎 Specific File Checks")

# Check for Python files
st.markdown("### Python Files")
python_files = [f for f in os.listdir('.') if f.endswith('.py')]
if python_files:
    for py_file in python_files:
        file_size = os.path.getsize(py_file)
        st.write(f"✅ **{py_file}** ({file_size} bytes)")
else:
    st.error("❌ No Python files found in root directory!")

# Check for data files
st.markdown("### Data Files (JSON)")
data_files = []
if os.path.exists('data'):
    data_files = [f for f in os.listdir('data') if f.endswith('.json')]
    for json_file in data_files:
        st.write(f"✅ data/{json_file}")
else:
    st.warning("⚠️ No 'data' folder found")

if not data_files:
    # Check if JSON files are in root
    root_json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    for json_file in root_json_files:
        st.write(f"✅ {json_file}")

# Check for asset files
st.markdown("### Asset Files (PNG)")
asset_files = []
if os.path.exists('assets'):
    asset_files = [f for f in os.listdir('assets') if f.endswith('.png')]
    for png_file in asset_files:
        st.write(f"✅ assets/{png_file}")
else:
    st.warning("⚠️ No 'assets' folder found")

if not asset_files:
    # Check if PNG files are in root
    root_png_files = [f for f in os.listdir('.') if f.endswith('.png')]
    for png_file in root_png_files:
        st.write(f"✅ {png_file}")

# Check for pages folder
st.markdown("### Pages Folder Structure")
if os.path.exists('pages'):
    st.success("✅ 'pages' folder exists")
    page_files = os.listdir('pages')
    for page_file in page_files:
        st.write(f"📄 pages/{page_file}")
elif os.path.exists('page'):
    st.success("✅ 'page' folder exists")
    page_files = os.listdir('page')
    for page_file in page_files:
        st.write(f"📄 page/{page_file}")
else:
    st.warning("⚠️ No 'pages' or 'page' folder found")

# Test specific app files we've been trying to use
st.subheader("🧪 Specific App File Tests")
target_files = [
    "app_mixing_p&id.py",
    "app_pressure_supply_p&id.py", 
    "app_DGS_SIM.py",
    "app_pressure_return_p&id.py",
    "app_separation_seal_p&id.py",
    "streamlit_app.py"
]

for target_file in target_files:
    exists = os.path.exists(target_file)
    status = "✅ EXISTS" if exists else "❌ MISSING"
    st.write(f"{status}: `{target_file}`")

# Check file permissions
st.subheader("🔐 File Permissions")
for target_file in target_files:
    if os.path.exists(target_file):
        try:
            with open(target_file, 'r') as f:
                first_line = f.readline()
                st.write(f"📖 `{target_file}`: {first_line.strip()}")
        except Exception as e:
            st.error(f"❌ Cannot read `{target_file}`: {e}")

# Environment info
st.subheader("🌐 Environment Information")
st.write(f"**Python Version:** {os.sys.version}")
st.write(f"**Streamlit Path:** {st.__file__}")
st.write(f"**User:** {os.getenv('USER', 'Unknown')}")

# Create a simple test to verify navigation
st.subheader("🚀 Navigation Test")
if st.button("Test Simple Navigation"):
    st.info("Testing basic Streamlit functionality...")
    st.success("✅ Streamlit is working!")
    
    # Test if we can switch to a file that definitely exists
    if os.path.exists("streamlit_app.py"):
        st.write("✅ streamlit_app.py exists - attempting navigation...")
        # st.switch_page("streamlit_app.py")  # This would refresh to same page
    else:
        st.error("❌ streamlit_app.py doesn't exist!")

st.markdown("---")
st.info("""
**Next Steps:**
1. Run this debug script: `streamlit run debug_structure.py`
2. Share the output screenshot with me
3. I'll give you the exact working solution based on your actual file structure
""")
