from src.storage.db import get_conn
import threading

class DecisionStore:
    _lock = threading.Lock()

    def __init__(self, db_path):
        self.db_path = db_path

    def log_decision(self, invoice_id, decision, confidence):
        # Open-per-write is safer + faster under threads
        with self._lock:
            conn = get_conn(self.db_path)
            conn.execute(
                """
                INSERT INTO decisions (invoice_id, decision, confidence)
                VALUES (?, ?, ?)
                """,
                (invoice_id, decision, confidence)
            )
            conn.close()
