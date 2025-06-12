import os

# Define paths for simulated database and audit log files

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# CONSTRAINT_DB_PATH = os.path.join(DATA_DIR, "constraints_db.json")
AUDIT_LOG_PATH = os.path.join(DATA_DIR, "audit_log.csv")

# --- Constants ---

ROLES = [
    "Marketing",
    "Finance",
    "Caustic Plant",
    "H2 Plant",
    "H2O2 Plant",
    "Flaker Plant",
    "ECH Plant",
    "Power Plant",
]

# Dummy constraints for each role
ROLE_CONSTRAINTS = {
    "Marketing": ["Budget Min", "Budget Max", "Campaign Target"],
    "Finance": ["Spending Limit", "Revenue Goal", "Profit Margin"],
    "Caustic Plant": ["Production Rate Min", "Production Rate Max", "Energy Usage"],
    "H2 Plant": ["H2 Purity Min", "H2 Pressure Max"],
    "H2O2 Plant": ["Concentration Min", "Flow Rate Max"],
    "Flaker Plant": ["Flaker Temp Min", "Flaker Temp Max", "Batch Size"],
    "ECH Plant": ["Reactor Temp Min", "Pressure Max"],
    "Power Plant": ["Power Output Min", "Efficiency Target"],
}

# Dummy hydrogen allocation data
HYDROGEN_ALLOCATION_DATA = {
    "Pipeline": {"allocated": 1500, "recommended": 1450, "status": "pending", "comment": ""},
    "Bank": {"allocated": 800, "recommended": 850, "status": "pending", "comment": ""},
    "HCL": {"allocated": 300, "recommended": 320, "status": "pending", "comment": ""},
    "Flaker - 1": {"allocated": 200, "recommended": 190, "status": "pending", "comment": ""},
    "Flaker - 2": {"allocated": 220, "recommended": 230, "status": "pending", "comment": ""},
    "Flaker - 3": {"allocated": 180, "recommended": 185, "status": "pending", "comment": ""},
    "Flaker - 4": {"allocated": 210, "recommended": 205, "status": "pending", "comment": ""},
    "H2O2": {"allocated": 400, "recommended": 390, "status": "pending", "comment": ""},
    "Boiler - P60": {"allocated": 600, "recommended": 610, "status": "pending", "comment": ""},
    "Boiler - P120": {"allocated": 550, "recommended": 540, "status": "pending", "comment": ""},
    "Vent": {"allocated": 50, "recommended": 60, "status": "pending", "comment": ""},
}
