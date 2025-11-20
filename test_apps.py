import streamlit as st
import os

st.set_page_config(layout="wide")
st.title("🧪 Test Individual Apps")

# Test if we can run the pressure supply app directly
st.subheader("Test Pressure Supply App")

# Method 1: Try importing directly
st.write("**Method 1: Direct import test**")
try:
    # Try to import and run the app
    import importlib.util
    spec = importlib.util.spec_from_file_location("pressure_app", "page/app_pressure_supply_p&id.py")
    pressure_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pressure_module)
    st.success("✅ Pressure supply app can be imported!")
except Exception as e:
    st.error(f"❌ Import failed: {e}")

# Method 2: Check file contents
st.write("**Method 2: File content check**")
try:
    with open("page/app_pressure_supply_p&id.py", "r") as f:
        first_lines = [f.readline() for _ in range(5)]
    st.write("First 5 lines of the file:")
    for i, line in enumerate(first_lines):
        st.write(f"{i+1}: {line.strip()}")
except Exception as e:
    st.error(f"❌ Cannot read file: {e}")

# Method 3: Test all apps
st.subheader("Test All Apps")
apps_to_test = [
    "app_mixing_p&id.py",
    "app_pressure_supply_p&id.py", 
    "app_DGS_SIM.py",
    "app_pressure_return_p&id.py",
    "app_separation_seal_p&id.py"
]

for app_file in apps_to_test:
    full_path = f"page/{app_file}"
    if os.path.exists(full_path):
        try:
            with open(full_path, "r") as f:
                content = f.read()
            # Check if it has the basic Streamlit structure
            has_st_import = "import streamlit" in content
            has_main_function = "def main()" in content or "if __name__" in content
            st.write(f"✅ **{app_file}**: {len(content)} chars, Streamlit: {has_st_import}, Main: {has_main_function}")
        except Exception as e:
            st.error(f"❌ **{app_file}**: Read error - {e}")
    else:
        st.error(f"❌ **{app_file}**: File not found")

# Method 4: Alternative navigation
st.subheader("Alternative Navigation")
st.info("If switch_page doesn't work, try running apps directly:")
st.code("streamlit run page/app_pressure_supply_p&id.py")
