import os
import glob

print("=== Looking for existing Reflex/UI files ===")

# Check for common Reflex patterns
patterns = [
    "**/*reflex*.py",
    "**/*rx*.py", 
    "**/ui/*.py",
    "**/components/*.py",
    "rxconfig.py",
    "reflex_app.py"
]

found_files = []
for pattern in patterns:
    matches = glob.glob(pattern, recursive=True)
    found_files.extend(matches)

if found_files:
    print("Found files:")
    for f in sorted(set(found_files)):
        print(f"  {f}")
else:
    print("No Reflex files found - this appears to be a new implementation")

# Check if there's a src/arete/ui directory (based on project structure)
ui_dir = "src/arete/ui"
if os.path.exists(ui_dir):
    print(f"\n=== {ui_dir} contents ===")
    for file in os.listdir(ui_dir):
        print(f"  {file}")
else:
    print(f"\n{ui_dir} does not exist")

# Also check for streamlit_app.py mentioned in instructions
streamlit_file = "src/arete/ui/streamlit_app.py"
if os.path.exists(streamlit_file):
    print(f"\nFound existing Streamlit app: {streamlit_file}")
    print("This suggests we need to create a parallel Reflex implementation")