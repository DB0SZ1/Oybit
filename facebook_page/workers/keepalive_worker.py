import time
import httpx
import os
import logging

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8000")
PING_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL", "600"))  # 10 minutes

def ping():
    try:
        response = httpx.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            logger.info({"event": "keepalive_ping", "status": "ok"})
        else:
            logger.warning({"event": "keepalive_ping", "status": response.status_code})
    except Exception as e:
        logger.error({"event": "keepalive_ping", "error": str(e)})

if __name__ == "__main__":
    import sys
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    logger.info({"event": "keepalive_start", "interval": PING_INTERVAL})
    while True:
        ping()
        time.sleep(PING_INTERVAL)
