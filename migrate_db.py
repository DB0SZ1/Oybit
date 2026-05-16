import sqlite3
import os

db_path = "c:/Users/IDRIS/Desktop/Oybit/oybit_dev.db"

if not os.path.exists(db_path):
    print("Database not found!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE posts ADD COLUMN narrative_simulation_result VARCHAR")
        print("Added narrative_simulation_result to posts")
    except Exception as e:
        print("Error adding narrative_simulation_result:", e)

    try:
        cursor.execute("ALTER TABLE posts ADD COLUMN narrative_simulation_confidence FLOAT")
        print("Added narrative_simulation_confidence to posts")
    except Exception as e:
        print("Error adding narrative_simulation_confidence:", e)
        
    try:
        cursor.execute("ALTER TABLE trend_signals ADD COLUMN status VARCHAR")
        print("Added status to trend_signals")
    except Exception as e:
        print("Error adding status to trend_signals:", e)
        
    try:
        cursor.execute("ALTER TABLE trend_signals ADD COLUMN recurring_style_context VARCHAR")
        print("Added recurring_style_context to trend_signals")
    except Exception as e:
        print("Error adding recurring_style_context to trend_signals:", e)

    conn.commit()
    conn.close()
    print("Migration complete.")
