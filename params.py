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
    # "ECH Plant",
    "Power Plant",
]

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


def get_constraints():
    ROLE_CONSTRAINTS = {
        "Marketing": ["Demand - H2O2 (TPH)", "Demand - Flaker (TPH)"],
        "Finance": ["Pipeline", "Bank", "H2O2", "Flaker", "Boiler", "HCl", "Vent"],  # in Rs/NM3
        "Caustic Plant": ["Total Caustic Production (TPH)",
                          "H2 generated (NM3) per ton of caustic",
                          "Total HCl Production (TPH)",
                          "H2 required (NM3) per ton of HCl"],

        "H2 Plant": ["Pipeline Compressor Capacity (NM3/hr)",
                     "Bank Compressor Capacity (NM3/hr)",
                     "Header Pressure Threshold (kgf/cm2)",
                     "Changeover time from pipeline to bank (hrs)"],

        "H2O2 Plant": ["H2O2 Production Capacity (TPH)",
                       "H2 (NM3) required per ton of H2O2",
                       "Load increase/decrease time for H2O2 (hrs)"],
        # "ECH Plant": ["Reactor Temp Min", "Pressure Max"],
        "Power Plant": ["P60 - H2 capacity",
                        "P120 - H2 capacity",
                        "P60 - Load inc/dec time (hrs)",
                        "P120 - Load inc/dec time (hrs)"
                        "Conversion: H2 (1 Nm3/hr) to Coal (X ton/hr)",
                        "Conversion: H2 (X Nm3) to H2 (1 ton)"],
    }

    flaker_constraints = []
    for i in range(1, 5):
        flaker_constraints.extend([
            f"Flaker-{i} Load Capacity (TPH)",
            f"Flaker-{i} H2 Specific Consumption (NM3/Ton)",
            f"Flaker-{i} NG Specific Consumption (SCM/Ton)",
        ])

    flaker_constraints.extend(["Flaker - Changeover time (NG to mix) (hrs)",
                               "Flaker - H2 load inc/dec time (hrs)"])
    ROLE_CONSTRAINTS["Flaker Plant"] = flaker_constraints
    return ROLE_CONSTRAINTS
