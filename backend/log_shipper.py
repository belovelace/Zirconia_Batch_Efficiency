import os
import time
import threading
import requests
import json
from typing import Optional

LOG_PATH = os.getenv("SERVER_ERRORS_LOG", "server_errors.log")
COLLECTOR_URL = os.getenv("LOG_COLLECTOR_URL")  # e.g. https://logs.example.com/ingest
BATCH_SIZE = int(os.getenv("LOG_SHIP_BATCH", "50"))
INTERVAL = int(os.getenv("LOG_SHIP_INTERVAL", "30"))  # seconds
POSITION_FILE = os.getenv("LOG_POSITION_FILE", ".server_errors.pos")
TIMEOUT = int(os.getenv("LOG_SHIP_TIMEOUT", "10"))


class LogShipper:
    def __init__(self, log_path: str = LOG_PATH, collector_url: Optional[str] = COLLECTOR_URL,
                 pos_file: str = POSITION_FILE, batch_size: int = BATCH_SIZE, interval: int = INTERVAL):
        self.log_path = log_path
        self.collector_url = collector_url
        self.pos_file = pos_file
        self.batch_size = batch_size
        self.interval = interval
        self._thread = None
        self._stop_event = threading.Event()

    def _read_position(self) -> int:
        try:
            with open(self.pos_file, "r", encoding="utf-8") as fh:
                return int(fh.read().strip() or 0)
        except Exception:
            return 0

    def _write_position(self, pos: int):
        try:
            with open(self.pos_file, "w", encoding="utf-8") as fh:
                fh.write(str(pos))
        except Exception:
            pass

    def _tail_batch(self):
        if not os.path.exists(self.log_path):
            return [], 0
        pos = self._read_position()
        lines = []
        new_pos = pos
        try:
            with open(self.log_path, "r", encoding="utf-8") as fh:
                fh.seek(pos)
                for _ in range(self.batch_size):
                    line = fh.readline()
                    if not line:
                        break
                    lines.append(line.strip())
                new_pos = fh.tell()
        except Exception:
            return [], pos
        return lines, new_pos

    def _ship(self, lines):
        if not self.collector_url:
            # nothing configured
            return True
        if not lines:
            return True
        # send as JSON array
        try:
            resp = requests.post(self.collector_url, json={"logs": lines}, timeout=TIMEOUT)
            return resp.status_code >= 200 and resp.status_code < 300
        except Exception:
            return False

    def _run_loop(self):
        while not self._stop_event.is_set():
            lines, new_pos = self._tail_batch()
            if lines:
                ok = self._ship(lines)
                if ok:
                    self._write_position(new_pos)
            # sleep interruptibly
            self._stop_event.wait(self.interval)

    def start(self):
        if self._thread is not None:
            return
        if not self.collector_url:
            # Not configured: do not start shipping thread, but allow position tracking in future
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="log_shipper")
        self._thread.start()

    def stop(self):
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None


# Singleton shipper
_shipper = LogShipper()

def start_shipper():
    _shipper.start()

def stop_shipper():
    _shipper.stop()
