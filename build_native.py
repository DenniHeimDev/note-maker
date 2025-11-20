import subprocess
import sys
import shutil
from pathlib import Path

def main():
    print("🔨 Building Note Maker Native App...")
    
    # 1. Check dependencies
    try:
        import PyInstaller
        import webview
    except ImportError:
        print("❌ Missing dependencies. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Clean previous builds
    print("🧹 Cleaning up old builds...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    # 3. Run PyInstaller
    print("📦 Bundling application...")
    try:
        subprocess.check_call([
            "pyinstaller", 
            "note_maker.spec", 
            "--noconfirm", 
            "--clean"
        ])
    except subprocess.CalledProcessError:
        print("❌ Build failed!")
        sys.exit(1)

    # 4. Success message
    print("\n✅ Build successful!")
    
    dist_dir = Path("dist/note-maker")
    if sys.platform == "win32":
        exe_path = dist_dir / "note-maker.exe"
        print(f"🚀 Run the app: {exe_path}")
    elif sys.platform == "darwin":
        app_path = Path("dist/note-maker.app")
        print(f"🚀 App bundle: {app_path}")
    else:
        # Linux
        exe_path = dist_dir / "note-maker"
        print(f"🚀 Run the app: {exe_path}")

if __name__ == "__main__":
    main()
