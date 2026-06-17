import os
import glob

def patch_db_session():
    search_pattern = r"c:\Users\IDRIS\Desktop\Oybit\*\db\session.py"
    files = glob.glob(search_pattern)
    
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "from sqlalchemy.pool import NullPool" not in content:
            # Import NullPool
            content = content.replace("from sqlalchemy import create_engine", "from sqlalchemy import create_engine\nfrom sqlalchemy.pool import NullPool")
            
            # Change engine_kwargs to use NullPool to fix Supabase 6543 pgbouncer drops
            content = content.replace(
                '"pool_size": 5,\n        "max_overflow": 10,\n        "pool_pre_ping": True,\n        "pool_recycle": 3600',
                '"poolclass": NullPool'
            )
            
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Patched {file} to use NullPool")

if __name__ == "__main__":
    patch_db_session()
