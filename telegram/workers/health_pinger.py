import os
import sys
import time
import urllib.request
import signal
from logger import get_logger

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logger = get_logger("health_pinger")
shutdown = False

def sigterm_handler(signum, frame):
    global shutdown
    logger.info("SIGTERM received. Shutting down health pinger...")
    shutdown = True

def run():
    signal.signal(signal.SIGTERM, sigterm_handler)
    
    # Internal API route
    url = os.getenv("FRONTEND_URL", "http://localhost:8000")
    health_url = f"{url}/api/health/"
    
    logger.info(f"Health pinger worker started. Pinging {health_url} roughly every 60s.")
    
    while not shutdown:
        try:
            res = urllib.request.urlopen(health_url, timeout=5)
            if res.status_code != 200:
                logger.warning(f"Health ping returned status: {res.status_code}")
        except Exception as e:
            logger.error(f"Health ping failed: {e}")
            
        for _ in range(60):
            if shutdown:
                break
            time.sleep(1)
            
    logger.info("Health pinger worker shut down gracefully.")

if __name__ == "__main__":
    run()
