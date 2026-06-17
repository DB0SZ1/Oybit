import os

BOT_PORTS = {
    "facebook_page": 8001,
    "facebook_personal": 8002,
    "instagram_brand": 8003,
    "instagram_personal": 8004,
    "linkedin": 8005,
    "reddit": 8006,
    "telegram": 8007
}

def fix_ports():
    for bot, port in BOT_PORTS.items():
        main_path = os.path.join(bot, "main.py")
        if not os.path.exists(main_path):
            continue
            
        with open(main_path, "r") as f:
            code = f.read()
            
        # Replace the hardcoded 8001 with the correct port
        if "os.environ.get('PORT', 8001)" in code:
            code = code.replace("os.environ.get('PORT', 8001)", f"os.environ.get('PORT', {port})")
            
            with open(main_path, "w") as f:
                f.write(code)
            print(f"Fixed port in {bot}/main.py to {port}")
        else:
            print(f"{bot}/main.py does not have the hardcoded 8001 or was already fixed")

if __name__ == "__main__":
    fix_ports()
