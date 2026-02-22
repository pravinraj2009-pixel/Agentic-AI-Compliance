import sqlite3

def get_conn(path):
    # Thread-safe connection (required for parallel execution)
    conn = sqlite3.connect(
        path,
        check_same_thread=False
    )

    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            invoice_id TEXT,
            decision TEXT,
            confidence REAL
        )
        """
    )

    # 🚀 CRITICAL PERFORMANCE INDEX
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_decisions_invoice_id
        ON decisions (invoice_id)
        """
    )

    conn.commit()
    return conn
