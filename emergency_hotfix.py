import os
import shutil
import subprocess

bots = [
    "facebook_page",
    "facebook_personal",
    "instagram_brand",
    "instagram_personal",
    "linkedin",
    "reddit",
    "telegram"
]

missing_files = [
    "config.py",
    "logger.py"
]

missing_dirs = [
    "intelligence",
    "token_store",
    "scheduler_worker",
    "feedback_loop",
    "growth",
    "analytics",
    "persona_engine",
    "publishers"
]

def hotfix():
    print("1. Restoring backend from git...")
    subprocess.run(["git", "checkout", "backend"], check=False)
    
    if not os.path.exists("backend"):
        print("ERROR: backend/ not found after git checkout. Cannot proceed.")
        return

    print("2. Distributing missing files/folders to all bots...")
    for bot in bots:
        # Copy missing files
        for f in missing_files:
            src = os.path.join("backend", f)
            dst = os.path.join(bot, f)
            if os.path.exists(src):
                shutil.copy2(src, dst)
        
        # Copy missing dirs
        for d in missing_dirs:
            src = os.path.join("backend", d)
            dst = os.path.join(bot, d)
            if os.path.exists(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                
    print("3. Replacing 'backend.' imports inside the bots...")
    for bot in bots:
        for root, dirs, files in os.walk(bot):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "backend." in content:
                        content = content.replace("from backend.", "from ")
                        content = content.replace("import backend.", "import ")
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)

    print("Hotfix complete!")

if __name__ == "__main__":
    hotfix()
