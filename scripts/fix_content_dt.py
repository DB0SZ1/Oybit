import os
import glob

def fix_content_datetime():
    search_pattern = r"c:\Users\IDRIS\Desktop\Oybit\*\api_routes\content.py"
    files = glob.glob(search_pattern)
    
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            
        if '"created_at": p.created_at,' in content:
            content = content.replace(
                '"created_at": p.created_at,',
                '"created_at": p.created_at.isoformat() if p.created_at else None,'
            )
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Patched {file}")

if __name__ == "__main__":
    fix_content_datetime()
