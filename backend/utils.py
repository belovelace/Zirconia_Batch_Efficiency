import traceback
import uuid
from datetime import datetime

LOG_PATH = "server_errors.log"


def log_exception(exc: Exception) -> str:
    """Log exception traceback to server_errors.log and return an error id."""
    err_id = str(uuid.uuid4())
    tb = traceback.format_exc()
    now = datetime.utcnow().isoformat() + "Z"
    entry = f"[{now}] ERROR_ID={err_id}\n{tb}\n\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except Exception:
        # best-effort logging; don't raise
        pass
    return err_id
