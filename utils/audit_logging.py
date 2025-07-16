# import datetime
#
# import pandas as pd
# import pytz
#
# from params import *
#
# AUDIT_LOG_PATH = os.path.join(DATA_DIR, "audit_log.csv")
#
#
# def load_audit_log():
#     """Loads the audit log from a CSV file."""
#     if not os.path.exists(AUDIT_LOG_PATH):
#         return pd.DataFrame(columns=["timestamp", "user", "role", "parameter", "old_value", "new_value", "comments"])
#     return pd.read_csv(AUDIT_LOG_PATH)
#
#
# def save_audit_log(df):
#     """Saves the audit log to a CSV file."""
#     df.to_csv(AUDIT_LOG_PATH, index=False)
#
#
# def log_audit_entry(user, role, parameter, old_value, new_value, comments=""):
#     """Adds an entry to the audit log."""
#     audit_df = load_audit_log()
#     ist = pytz.timezone('Asia/Kolkata')
#     timestamp = datetime.datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
#     new_entry = pd.DataFrame([{
#         "timestamp": timestamp,
#         "user": user,
#         "role": role,
#         "parameter": parameter,
#         "old_value": old_value,
#         "new_value": new_value,
#         "comments": comments
#     }])
#     audit_df = pd.concat([audit_df, new_entry], ignore_index=True)
#     save_audit_log(audit_df)


import datetime
import sqlite3

import pandas as pd
import pytz

from params import *


def initialize_audit_log_table():
    """Creates the audit_log table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                timestamp TEXT,
                user TEXT,
                role TEXT,
                parameter TEXT,
                old_value TEXT,
                new_value TEXT,
                comments TEXT
            )
        """)
        conn.commit()


def load_audit_log():
    """Loads the audit log from the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)


def save_audit_log(df):
    """Saves the audit log DataFrame to the SQLite database (overwrite mode)."""
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)


def log_audit_entry(user, role, parameter, old_value, new_value, comments=""):
    """Adds a new entry to the audit log table."""
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"""
            INSERT INTO {TABLE_NAME} (timestamp, user, role, parameter, old_value, new_value, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, user, role, parameter, old_value, new_value, comments))
        conn.commit()

