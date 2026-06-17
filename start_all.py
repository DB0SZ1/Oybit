import os
import sys
import subprocess
import time

def main():
    print("=== Oybit Universal Launcher ===")
    
    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    
    # 1. Start Auto Watcher (Dummy port 10323)
    watcher_script = os.path.join(os.getcwd(), "auto_watcher.py")
    if os.path.exists(watcher_script):
        print("[*] Launching auto_watcher.py in background...")
        # using pythonw to avoid opening a console window, or just python with CREATE_NO_WINDOW
        subprocess.Popen(
            [sys.executable, "auto_watcher.py"],
            cwd=os.getcwd(),
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
        )
    else:
        print("[!] auto_watcher.py not found!")

    # 2. Start FastAPI Backend (Port 10321)
    backend_dir = os.path.join(os.getcwd(), "hf_deploy")
    if os.path.exists(backend_dir):
        print("[*] Launching Oybit API Backend on port 10321 in background...")
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10321"],
            cwd=backend_dir,
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS
        )
    else:
        print("[!] hf_deploy directory not found!")
        
    print("")
    print("[+] Successfully launched both processes in the background!")
    print("[+] They will run eternally even if you close this terminal.")
    print("")
    print("To stop them, open a Command Prompt and run:")
    print("  FOR BACKEND:  for /f \"tokens=5\" %a in ('netstat -aon ^| find \":10321\"') do taskkill /f /pid %a")
    print("  FOR WATCHER:  for /f \"tokens=5\" %a in ('netstat -aon ^| find \":10323\"') do taskkill /f /pid %a")
    print("================================")
    
if __name__ == "__main__":
    main()
