#!/usr/bin/env python3
"""
Launch script for Arete Streamlit interface.

Usage:
    python run_streamlit.py

This will start the Streamlit web interface for the Arete philosophical
tutoring system on http://localhost:8501
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit app."""
    # Get the path to the Streamlit app
    app_path = Path(__file__).parent / "src" / "arete" / "ui" / "streamlit_app.py"
    
    # Check if app file exists
    if not app_path.exists():
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)
    
    # Launch Streamlit
    try:
        print("🏛️  Starting Arete Philosophy Tutor...")
        print("📝  Interface will open at: http://localhost:8501")
        print("⏹️  Press Ctrl+C to stop")
        print("-" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--theme.base", "light",
            "--theme.primaryColor", "#007bff",
            "--theme.backgroundColor", "#ffffff",
            "--theme.secondaryBackgroundColor", "#f8f9fa"
        ], check=True)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Thanks for using Arete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Streamlit not found. Install it with: pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()