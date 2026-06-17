import os
import re

BOT_DIRS = [
    "facebook_page", "facebook_personal", "instagram_brand", 
    "instagram_personal", "linkedin", "reddit", "telegram"
]

def fix_main_py():
    for bot in BOT_DIRS:
        main_path = os.path.join(bot, "main.py")
        if not os.path.exists(main_path):
            continue
            
        with open(main_path, "r") as f:
            code = f.read()
            
        if "uvicorn.run(app" not in code:
            code = code.replace(
                "    t = threading.Thread(target=worker_loop, daemon=True)\n    t.start()\n",
                "    t = threading.Thread(target=worker_loop, daemon=True)\n    t.start()\n\n    port = int(os.environ.get('PORT', 8001))\n    logger.info(f'Starting Mini-API on port {port}')\n    uvicorn.run(app, host='0.0.0.0', port=port)\n"
            )
            
            with open(main_path, "w") as f:
                f.write(code)
            print(f"Fixed uvicorn.run in {bot}/main.py")
        else:
            print(f"{bot}/main.py already has uvicorn.run")

if __name__ == "__main__":
    fix_main_py()
