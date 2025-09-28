#!/usr/bin/env python3
import subprocess
import sys
import os

# Change to the arete directory
os.chdir("D:\\Coding\\arete")

# Run the fix script
try:
    result = subprocess.run([sys.executable, "fix_icons.py"], capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Return code: {result.returncode}")
except Exception as e:
    print(f"Error running script: {e}")