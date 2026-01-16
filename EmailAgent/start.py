#!/usr/bin/env python
"""
🚀 QUICKSTART - GeniOS Email Agent GUI
Run this to launch the Email Agent interface
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║              📧 GeniOS Email Agent 📧                ║
    ║                                                       ║
    ║         AI-Powered Inbox Intelligence System          ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    print("🚀 Starting Email Agent GUI...")
    print("=" * 60)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✓ Streamlit found")
    except ImportError:
        print("❌ Streamlit not installed")
        print("   Installing now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Get paths
    script_dir = Path(__file__).parent
    gui_app = script_dir / "gui_app.py"
    
    if not gui_app.exists():
        print(f"❌ Error: gui_app.py not found at {gui_app}")
        return
    
    print(f"✓ GUI App: {gui_app}")
    print("=" * 60)
    print("\n📧 Opening Email Agent in your browser...")
    print("   URL: http://localhost:8501")
    print("\n💡 Features:")
    print("   • Dashboard - Overview of your inbox")
    print("   • Priority Inbox - Organized by importance")
    print("   • Compose Email - AI-assisted drafting")
    print("   • Analytics - Performance metrics")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Change to script directory
    os.chdir(script_dir)
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(gui_app),
            "--server.headless=false",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Email Agent GUI stopped successfully!")
        print("   Thank you for using GeniOS Email Agent 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Try running manually:")
        print(f"   cd {script_dir}")
        print(f"   streamlit run gui_app.py")

if __name__ == "__main__":
    main()
