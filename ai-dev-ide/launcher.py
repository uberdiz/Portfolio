"""
Fast launcher for AI Dev IDE
"""
import os
import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required = ["requests", "tkinter"]
    missing = []
    
    for package in required:
        try:
            if package == "tkinter":
                import tkinter
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def main():
    print("🚀 AI Dev IDE - Modular Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("⚠️  Warning: app.py not found in current directory")
        print("   Current dir:", os.getcwd())
        print("   Looking for: app.py, gui/, agents/, core/")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Installing requirements...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        except:
            print("Could not install from requirements.txt")
            print("Please install manually: pip install requests")
    
    # Check if setup guide should run
    settings_path = os.path.join(os.path.expanduser("~"), ".ai_dev_ide_settings.json")
    if not os.path.exists(settings_path):
        print("\n📋 First time setup detected!")
        choice = input("Run setup guide? (y/n): ")
        if choice.lower() == 'y':
            try:
                subprocess.run([sys.executable, "setup_free_apis.py"])
            except:
                print("Setup guide not found.")
    
    # Launch the app
    print("\n🎯 Launching AI Dev IDE...")
    try:
        import app
        app.main()
    except Exception as e:
        print(f"Error launching app: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()