"""
Quick launcher for GeniOS Email Agent GUI
"""
import subprocess
import sys
from pathlib import Path

def main():
    print("🚀 Starting GeniOS Email Agent GUI...")
    print("=" * 60)
    
    # Get the path to the GUI app
    gui_app = Path(__file__).parent / "gui_app.py"
    
    # Get Python executable
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment
        python_exe = sys.executable
    else:
        python_exe = sys.executable
    
    print(f"✓ Python: {python_exe}")
    print(f"✓ GUI App: {gui_app}")
    print("=" * 60)
    print("\n📧 The Email Agent GUI will open in your browser...")
    print("   URL: http://localhost:8501")
    print("\n⚠️  Press Ctrl+C to stop the server\n")
    
    # Run streamlit
    try:
        subprocess.run([
            python_exe, "-m", "streamlit", "run", str(gui_app),
            "--server.headless=true"
        ])
    except KeyboardInterrupt:
        print("\n\n✓ Email Agent GUI stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTry running manually:")
        print(f"   {python_exe} -m streamlit run {gui_app}")

if __name__ == "__main__":
    main()
