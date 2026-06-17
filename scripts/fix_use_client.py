import os

bot_components_dir = r"Frontend Dashbaord\components\bots"

for filename in os.listdir(bot_components_dir):
    if filename.endswith(".tsx"):
        filepath = os.path.join(bot_components_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.startswith('"use client"'):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write('"use client"\n\n' + content)
