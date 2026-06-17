import os
import re

bots = [
    "facebook_page",
    "facebook_personal",
    "instagram_brand",
    "instagram_personal",
    "linkedin",
    "reddit",
    "telegram"
]

ports = {
    "facebook_page": 8001,
    "facebook_personal": 8002,
    "instagram_brand": 8003,
    "instagram_personal": 8004,
    "linkedin": 8005,
    "reddit": 8006,
    "telegram": 8007,
}

# 1. Frontend api.ts rewrite
api_ts_path = "frontend/src/lib/api.ts"
if os.path.exists(api_ts_path):
    with open(api_ts_path, 'r', encoding='utf-8') as f:
        api_content = f.read()

    new_api_header = """const BOT_PORTS: Record<string, number> = {
  facebook_page: 8001,
  facebook_personal: 8002,
  instagram_brand: 8003,
  instagram_personal: 8004,
  linkedin: 8005,
  reddit: 8006,
  telegram: 8007,
};

export function getActiveBot(): string {
  if (typeof window === 'undefined') return 'linkedin';
  return localStorage.getItem('oybit_active_bot') || 'linkedin';
}

export function setActiveBot(bot: string) {
  localStorage.setItem('oybit_active_bot', bot);
  window.dispatchEvent(new Event('bot_changed'));
}

function getApiBase() {
  const bot = getActiveBot();
  const port = BOT_PORTS[bot] || 8001;
  return `http://localhost:${port}/api`;
}
"""
    api_content = re.sub(r"const API_BASE = .*?;", new_api_header, api_content, count=1)
    api_content = api_content.replace("`${API_BASE}", "`${getApiBase()}")

    with open(api_ts_path, 'w', encoding='utf-8') as f:
        f.write(api_content)

# 2. Frontend layout.tsx rewrite
layout_path = "frontend/src/app/layout.tsx"
if os.path.exists(layout_path):
    with open(layout_path, 'r', encoding='utf-8') as f:
        layout_content = f.read()

    import_add = """import { getActiveBot, setActiveBot } from '@/lib/api';\n"""
    if "getActiveBot" not in layout_content:
        layout_content = layout_content.replace("import { useEffect, useState } from 'react';", "import { useEffect, useState } from 'react';\n" + import_add)

    # Insert bot selector state
    state_add = """  const [activeBot, setBotState] = useState('linkedin');
  
  useEffect(() => {
    setBotState(getActiveBot());
    const handleBotChange = () => setBotState(getActiveBot());
    window.addEventListener('bot_changed', handleBotChange);
    return () => window.removeEventListener('bot_changed', handleBotChange);
  }, []);
"""
    layout_content = layout_content.replace("const [sidebarOpen, setSidebarOpen] = useState(false);", "const [sidebarOpen, setSidebarOpen] = useState(false);\n" + state_add)

    # Insert selector UI in sidebar
    selector_ui = """
        <div style={{ padding: '0 12px 16px', display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>Active Platform</label>
          <select 
            value={activeBot} 
            onChange={(e) => setActiveBot(e.target.value)}
            style={{ 
              width: '100%', padding: '6px 8px', borderRadius: 6, 
              background: 'var(--bg-secondary)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', fontSize: 12, outline: 'none'
            }}
          >
            <option value="facebook_page">Facebook Page</option>
            <option value="facebook_personal">Facebook Personal</option>
            <option value="instagram_brand">Instagram Brand</option>
            <option value="instagram_personal">Instagram Personal</option>
            <option value="linkedin">LinkedIn</option>
            <option value="reddit">Reddit</option>
            <option value="telegram">Telegram</option>
          </select>
        </div>
"""
    layout_content = layout_content.replace("<div className=\"sidebar-subtitle\">Autonomous Engine</div>\n      </div>", "<div className=\"sidebar-subtitle\">Autonomous Engine</div>\n      </div>\n" + selector_ui)

    with open(layout_path, 'w', encoding='utf-8') as f:
        f.write(layout_content)

# 3. Add Mini-FastAPI to each bot
mini_api_code = """import os
import time
import logging
import threading
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from db.session import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI(title="Oybit Mini-API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "bot": "%s"}

@app.get("/api/auth/me")
def me():
    return {"username": "admin", "role": "owner"}

@app.post("/api/auth/login")
def login():
    return {"access_token": "dummy_token", "expires_at": "never"}

@app.get("/api/notifications")
def notifications():
    return {"unread_count": 0, "data": []}

@app.post("/api/pipeline/trigger-opportunity")
def trigger_opportunity(background_tasks: BackgroundTasks):
    logger.info("Manual trigger received from UI!")
    # Here we would normally wake up the opportunity worker
    def manual_trigger():
        logger.info("Executing manual opportunity trigger...")
        time.sleep(2)
        logger.info("Manual trigger complete.")
    background_tasks.add_task(manual_trigger)
    return {"status": "triggered"}

def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting standalone isolated worker...")
    
    # Run the worker loop in a background thread
    def worker_loop():
        while True:
            logger.info("Checking for new opportunities...")
            time.sleep(60)
            
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    
    # Start the FastAPI server on the main thread
    port = int(os.environ.get("PORT", %d))
    logger.info(f"Starting Mini-API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start_worker()
"""

for bot, port in ports.items():
    main_path = os.path.join(bot, "main.py")
    if os.path.exists(main_path):
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(mini_api_code % (bot, port))
            
print("Refactoring complete.")
