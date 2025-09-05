try:
    with open("src/arete/ui/streamlit_app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    print("=== STREAMLIT APP FOUND ===")
    print(f"File size: {len(content)} characters")
    
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Show imports to understand dependencies
    print("\n=== IMPORTS ===")
    for i, line in enumerate(lines[:50]):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            print(f"{i+1:2d}: {line}")
    
    # Look for key patterns
    patterns = ['def ', 'class ', '@st.', 'st.', 'rx.', 'reflex']
    print(f"\n=== KEY PATTERNS ===")
    for i, line in enumerate(lines[:100]):
        for pattern in patterns:
            if pattern in line:
                print(f"{i+1:2d}: {line.strip()}")
                break

except FileNotFoundError:
    print("Streamlit app not found - proceeding with new Reflex implementation")
except Exception as e:
    print(f"Error: {e}")