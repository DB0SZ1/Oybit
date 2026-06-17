import os
import glob

def fix_shadowed_endpoints():
    search_pattern = r"c:\Users\IDRIS\Desktop\Oybit\*\main.py"
    files = glob.glob(search_pattern)
    
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        new_lines = []
        skip = False
        for line in lines:
            if '@app.get("/api/pipeline/posts")' in line:
                skip = True
                continue
            if skip:
                if 'def pipeline_posts' in line:
                    continue
                if 'return {"posts": []}' in line:
                    skip = False
                    continue
            new_lines.append(line)
            
        with open(file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Patched {file}")

if __name__ == "__main__":
    fix_shadowed_endpoints()
