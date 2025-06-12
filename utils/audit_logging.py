import datetime
import pandas as pd

from params import *

AUDIT_LOG_PATH = os.path.join(DATA_DIR, "audit_log.csv")


def load_audit_log():
    """Loads the audit log from a CSV file."""
    if not os.path.exists(AUDIT_LOG_PATH):
        return pd.DataFrame(columns=["timestamp", "user", "role", "parameter", "old_value", "new_value", "comments"])
    return pd.read_csv(AUDIT_LOG_PATH)


def save_audit_log(df):
    """Saves the audit log to a CSV file."""
    df.to_csv(AUDIT_LOG_PATH, index=False)


def log_audit_entry(user, role, parameter, old_value, new_value, comments=""):
    """Adds an entry to the audit log."""
    audit_df = load_audit_log()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([{
        "timestamp": timestamp,
        "user": user,
        "role": role,
        "parameter": parameter,
        "old_value": old_value,
        "new_value": new_value,
        "comments": comments
    }])
    audit_df = pd.concat([audit_df, new_entry], ignore_index=True)
    save_audit_log(audit_df)
