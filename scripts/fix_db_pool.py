import os
import glob

def patch_db_engines():
    search_pattern = r"c:\Users\IDRIS\Desktop\Oybit\*\db\models.py"
    files = glob.glob(search_pattern)
    
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "pool_pre_ping=True" not in content and "create_engine(" in content:
            # We add pool_pre_ping and pool_recycle to fix the connection dropping error
            content = content.replace(
                "create_engine(database_url, echo=False)",
                "create_engine(database_url, echo=False, pool_pre_ping=True, pool_recycle=300)"
            )
            
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Patched {file}")

if __name__ == "__main__":
    patch_db_engines()
