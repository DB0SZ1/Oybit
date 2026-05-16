import logging
import json
import os
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        # If context dict was passed, merge it
        if hasattr(record, 'context') and isinstance(record.context, dict):
            # Mask sensitive fields
            safe_context = mask_sensitive(record.context)
            log_entry.update(safe_context)
        return json.dumps(log_entry, ensure_ascii=True)

SENSITIVE_KEYS = {
    "access_token", "refresh_token", "token", "secret", "password",
    "api_key", "client_secret", "app_secret", "persona_content"
}

def mask_sensitive(data: dict) -> dict:
    result = {}
    for k, v in data.items():
        if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
            result[k] = "***MASKED***"
        elif isinstance(v, dict):
            result[k] = mask_sensitive(v)
        else:
            result[k] = v
    return result

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return logger

def setup_global_logging():
    """Call this on application startup to force JSON logging everywhere."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            handler.setFormatter(JSONFormatter())
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        root_logger.addHandler(handler)
        root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
