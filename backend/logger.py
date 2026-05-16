import os
import json
import logging
import re
from datetime import datetime
from backend.config import DISPLAY_TIMEZONE, to_display_time

# Tokens to mask in logs
SENSITIVE_KEYS = [
    r"EAAG\w+",  # Facebook/Meta tokens
    r"IGQ\w+",   # Instagram tokens
    r"sk-or-v1-\w+", # OpenRouter tokens
    r"Bearer\s+[\w\-._]+", # Generic bearer tokens
    r"eyJ\w+\.\w+\.\w+" # JWT headers/tokens
]

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    Masks sensitive tokens automatically.
    """
    def __init__(self, **kwargs):
        super().__init__()

    def _mask_sensitive_data(self, message: str) -> str:
        if not isinstance(message, str):
            return message
        for pattern in SENSITIVE_KEYS:
            message = re.sub(pattern, "[MASKED]", message)
        return message

    def format(self, record: logging.LogRecord) -> str:
        # Use timezone-aware time for display
        dt = to_display_time(datetime.utcnow())
        
        message = record.getMessage()
        if hasattr(record, "msg_dict") and isinstance(record.msg_dict, dict):
            # Support passing a dict directly to the logger
            msg_str = json.dumps(record.msg_dict)
        else:
            msg_str = message

        msg_str = self._mask_sensitive_data(msg_str)

        log_obj = {
            "timestamp": dt.isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg_str,
            "module": record.module,
            "line": record.lineno,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured JSON logger. Always use this instead of print or default logging.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to avoid duplicates
    if not logger.handlers:
        logger.setLevel(level)
        logger.propagate = False
        
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = JSONFormatter()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
