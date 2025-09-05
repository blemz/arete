import os

# Check if streamlit app exists (mentioned in project instructions)
streamlit_path = os.path.join("src", "arete", "ui", "streamlit_app.py")
print(f"Checking for Streamlit app: {streamlit_path}")
print(f"Exists: {os.path.exists(streamlit_path)}")

# Check for rxconfig.py (main Reflex config)
rxconfig_path = "rxconfig.py"
print(f"\nChecking for Reflex config: {rxconfig_path}")
print(f"Exists: {os.path.exists(rxconfig_path)}")

# Check src structure
src_path = "src"
if os.path.exists(src_path):
    print(f"\n=== Source structure ===")
    for root, dirs, files in os.walk(src_path):
        if "arete" in root and "ui" in root:
            print(f"Directory: {root}")
            for file in files:
                if file.endswith('.py'):
                    print(f"  Python file: {file}")

# List all .py files in root that might be relevant
root_files = [f for f in os.listdir('.') if f.endswith('.py')]
print(f"\nPython files in root directory:")
for f in sorted(root_files):
    print(f"  {f}")