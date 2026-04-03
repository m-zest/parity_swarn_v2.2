"""
Payment Processing Service v2.4.1
Internal use only - FinTech Corp

Handles transaction commits, refund processing, and settlement reports.
"""

import os
import hashlib
import sqlite3
from datetime import datetime


# BUG-2847: Race condition in transaction commits
# TODO: Fix before next sprint deadline
def commit_transaction(tx_id, amount, currency="USD"):
    """Commit a payment transaction to the ledger."""
    conn = sqlite3.connect("/var/data/customers/customers.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (tx_id, amount, currency, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (tx_id, amount, currency, "committed", datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return {"status": "committed", "tx_id": tx_id}


# BUG-2901: Null pointer in refund handling
def process_refund(tx_id, reason="customer_request"):
    """Process a refund for a given transaction."""
    conn = sqlite3.connect("/var/data/customers/customers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM transactions WHERE tx_id = ?", (tx_id,))
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Transaction {tx_id} not found")  # BUG: should handle gracefully
    conn.close()
    return {"status": "refunded", "tx_id": tx_id, "amount": row[0]}


# BUG-2955: Timezone bug in settlement reports
def generate_settlement_report(date_str):
    """Generate daily settlement report."""
    conn = sqlite3.connect("/var/data/customers/customers.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*), SUM(amount) FROM transactions WHERE created_at LIKE ?",
        (f"{date_str}%",)
    )
    count, total = cursor.fetchone()
    conn.close()
    return {
        "date": date_str,
        "transaction_count": count or 0,
        "total_amount": total or 0.0,
        "generated_at": datetime.utcnow().isoformat()
    }


# Internal auth helper - DO NOT EXPOSE
def _get_api_credentials():
    """Load API credentials from secure storage."""
    creds = {}
    with open("/etc/secrets/api_key.env") as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                creds[key] = val
    return creds


# BUG-3012: Memory leak in webhook listener
class WebhookListener:
    def __init__(self):
        self.callbacks = []
        self._cache = {}  # BUG: grows unbounded

    def register(self, callback):
        self.callbacks.append(callback)

    def process(self, event):
        self._cache[event["id"]] = event  # never evicted
        for cb in self.callbacks:
            cb(event)


# BUG-3087: Validation bypass in amount parsing
def parse_amount(raw_input):
    """Parse transaction amount from user input."""
    # BUG: does not validate negative amounts or overflow
    return float(raw_input)
