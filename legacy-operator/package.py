import subprocess
import sys
import os

print("DEPRECATED: This is the old customtkinter GUI build.")
print("Use the modern one-stop .exe instead:")
print("  python package.py          # produces dist/rdn.exe + rdn-portable.zip")
print("  (or py -3.13 install.py --build)")
print("The new rdn.exe is the full coherent harness with dashboard, metrics, tray, CLI, and Xchange support.")
print("The old desktop GUI has been superseded by the new Streamlit harness (rdn.dash).")

def build_exe():
    print("\n(Old build path left for reference. Run the root package.py for the real one-stop EXE.)")

if __name__ == "__main__":
    build_exe()
