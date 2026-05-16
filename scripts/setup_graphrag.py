"""
Oybit — setup_graphrag.py (GAPS_FINAL GAP 7.2)
Bootstrap script to initialize the GraphRAG knowledge graph.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mirofish.stability import check_graphrag_initialized, initialize_graphrag

def main():
    persona_path = os.getenv("PERSONA_PATH", "personas/ahmad/persona.md")
    
    if check_graphrag_initialized():
        print("[INFO] GraphRAG already initialized.")
        return
    
    print("[INFO] Initializing GraphRAG...")
    
    if not os.path.exists(persona_path):
        print(f"[WARN] Persona file not found at {persona_path}, creating with defaults...")
        os.makedirs(os.path.dirname(persona_path), exist_ok=True)
        with open(persona_path, 'w', encoding='utf-8') as f:
            f.write("# Ahmad — Default Persona\n\n## Topics\n- Technology\n- Entrepreneurship\n- Product Development\n")
    
    index = initialize_graphrag(persona_path)
    print(f"[PASS] GraphRAG initialized with {len(index.get('nodes', []))} topic nodes.")

if __name__ == "__main__":
    main()
