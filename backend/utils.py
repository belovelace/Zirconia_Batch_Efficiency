import traceback
import uuid
from datetime import datetime
import json
import os

LOG_PATH = os.getenv("SERVER_ERRORS_LOG", "server_errors.log")


def log_exception(exc: Exception) -> str:
    """Log exception traceback to server_errors.log as a JSON line and return an error id.

    Each line is a JSON object with: id, timestamp, type, message, traceback
    """
    err_id = str(uuid.uuid4())
    tb = traceback.format_exc()
    now = datetime.utcnow().isoformat() + "Z"
    entry = {
        "id": err_id,
        "timestamp": now,
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": tb,
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # best-effort logging; don't raise
        pass
    return err_id
