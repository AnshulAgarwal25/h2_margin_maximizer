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
    "Dashboard"
]

# Dummy hydrogen allocation data
HYDROGEN_ALLOCATION_DATA = {
    "Pipeline": {"allocated": 8800, "recommended": 8750, "status": "accepted", "comment": "", "min_constrained": 0,
                 "max_constrained": 12000},
    "Bank": {"allocated": 0, "recommended": 0, "status": "accepted", "comment": "", "min_constrained": 0,
             "max_constrained": 10000},
    "HCL": {"allocated": 18.75, "recommended": 18.75, "status": "accepted", "comment": "", "min_constrained": 0,
            "max_constrained": 1200},
    "Flaker - 1": {"allocated": 0, "recommended": 0, "status": "accepted", "comment": "", "min_constrained": 0,
                   "max_constrained": 1200},
    "Flaker - 2": {"allocated": 0, "recommended": 0, "status": "accepted", "comment": "", "min_constrained": 0,
                   "max_constrained": 1200},
    "Flaker - 3": {"allocated": 9, "recommended": 10, "status": "accepted", "comment": "", "min_constrained": 0,
                   "max_constrained": 1200},
    "Flaker - 4": {"allocated": 9, "recommended": 10, "status": "accepted", "comment": "", "min_constrained": 0,
                   "max_constrained": 1200},
    "H2O2": {"allocated": 4, "recommended": 3.34, "status": "accepted", "comment": "", "min_constrained": 0,
             "max_constrained": 1200},
    "Boiler - P60": {"allocated": 600, "recommended": 610, "status": "accepted", "comment": "", "min_constrained": 0,
                     "max_constrained": 1200},
    "Boiler - P120": {"allocated": 550, "recommended": 540, "status": "accepted", "comment": "", "min_constrained": 0,
                      "max_constrained": 1200},
    "Vent": {"allocated": 0, "recommended": 0, "status": "accepted", "comment": "", "min_constrained": 0,
             "max_constrained": 1200},
}

entry_constraints_dummy = {
    'Marketing': {'Demand - H2O2 (TPD)': {'min': 80, 'max': 80},
                  'Demand - Flaker (TPD)': {'min': 400, 'max': 450}},

    'Finance': {'Pipeline': 20, 'Bank': 20, 'H2O2': 6, 'Flaker': 19, 'Boiler': 4, 'HCl': 0, 'Vent': 0},

    'Caustic Plant': {'Duration of pipeline demand change (hrs)': 0,
                      'Total Caustic Production (TPD)': {'min': 0, 'max': 2225},
                      'H2 generated (NM3) per ton of caustic': 280,
                      'Total HCl Production (TPD)': {'min': 0, 'max': 450}, 'H2 required (NM3) per ton of HCl': 365},

    'H2 Plant': {'Pipeline Compressor Capacity (NM3/hr)': {'min': 0, 'max': 12000},
                 'Bank Compressor Capacity (NM3/hr)': {'min': 0, 'max': 8000},
                 'Header Pressure Threshold (kgf/cm2)': {'min': 35, 'max': 125},
                 'Changeover time from pipeline to bank (hrs)': 0.1},

    'H2O2 Plant': {'H2O2 Production Capacity (TPD)': {'min': 75, 'max': 150},
                   'H2 (NM3) required per ton of H2O2': 710,
                   'Load increase/decrease time for H2O2 (hrs)': 8},

    'Flaker Plant': {'Flaker-1 Load Capacity (TPD)': {'min': 70, 'max': 100},
                     'Flaker-1 H2 Specific Consumption (NM3/Ton)': 347, 'Flaker-1 NG Specific Consumption (SCM/Ton)': 0,
                     'Flaker-2 Load Capacity (TPD)': {'min': 140, 'max': 200},
                     'Flaker-2 H2 Specific Consumption (NM3/Ton)': 230, 'Flaker-2 NG Specific Consumption (SCM/Ton)': 0,
                     'Flaker-3 Load Capacity (TPD)': {'min': 200, 'max': 300},
                     'Flaker-3 H2 Specific Consumption (NM3/Ton)': 220,
                     'Flaker-3 NG Specific Consumption (SCM/Ton)': 67,
                     'Flaker-4 Load Capacity (TPD)': {'min': 200, 'max': 300},
                     'Flaker-4 H2 Specific Consumption (NM3/Ton)': 220,
                     'Flaker-4 NG Specific Consumption (SCM/Ton)': 67,
                     'Flaker - Changeover time (NG to mix) (hrs)': 0.5, 'Flaker - H2 load inc/dec time (hrs)': 0.2
                     },

    'Power Plant': {'P60 - H2 capacity': {'min': 900, 'max': 3500},
                    'P120 - H2 capacity': {'min': 1500, 'max': 6000},
                    'P60 - Load inc/dec time (hrs)': 0.3, 'P120 - Load inc/dec time (hrs)': 0.5,
                    'Conversion: H2 (1 Nm3/hr) to Coal (X ton/hr)': 1000 / 0.56,
                    'Conversion: H2 (X Nm3) to H2 (1 ton)': 0.09 / 1000},
    'Dashboard': {}
}

dcs_constraints_dummy = {
    "caustic_production": 70.8,
    "pipeline_flow": 8750,
    "header_pressure": 100,
    "bank_available": 0,
    'hcl_production': 18.75,
    "h2o2_production": 3.34,
    "flaker-1_load": 0,
    "flaker-2_load": 0,
    "flaker-3_load": 10,
    "flaker-4_load": 10,
    "boiler_p60_run": 1,
    "boiler_p120_run": 1,
}

key_mapping = {
    "Pipeline": "pipeline",
    "Bank": "bank",
    "HCL": "hcl",
    "Flaker - 1": "flaker-1",
    "Flaker - 2": "flaker-2",
    "Flaker - 3": "flaker-3",
    "Flaker - 4": "flaker-4",
    "H2O2": "h2o2",
    "Boiler - P60": "boiler_p60",
    "Boiler - P120": "boiler_p120",
    "Vent": "vent"
}


def get_constraints():
    ROLE_CONSTRAINTS = {
        "Marketing": [
            {"name": "Demand - H2O2 (TPD)", "type": "range"},
            {"name": "Demand - Flaker (TPD)", "type": "range"}
        ],
        "Finance": [
            {"name": "Pipeline", "type": "single"},
            {"name": "Bank", "type": "single"},
            {"name": "H2O2", "type": "single"},
            {"name": "Flaker", "type": "single"},
            {"name": "Boiler", "type": "single"},
            {"name": "HCl", "type": "single"},
            {"name": "Vent", "type": "single"}
        ],
        "Caustic Plant": [
            {"name": "Duration of pipeline demand change (hrs)", "type": "single"},
            {"name": "Total Caustic Production (TPD)", "type": "range"},
            {"name": "H2 generated (NM3) per ton of caustic", "type": "single"},
            {"name": "Total HCl Production (TPD)", "type": "range"},
            {"name": "H2 required (NM3) per ton of HCl", "type": "single"}
        ],
        "H2 Plant": [
            {"name": "Pipeline Compressor Capacity (NM3/hr)", "type": "range"},
            {"name": "Bank Compressor Capacity (NM3/hr)", "type": "range"},
            {"name": "Header Pressure Threshold (kgf/cm2)", "type": "range"},
            {"name": "Changeover time from pipeline to bank (hrs)", "type": "single"}
        ],
        "H2O2 Plant": [
            {"name": "H2O2 Production Capacity (TPD)", "type": "range"},
            {"name": "H2 (NM3) required per ton of H2O2", "type": "single"},
            {"name": "Load increase/decrease time for H2O2 (hrs)", "type": "single"}
        ],
        "Power Plant": [
            {"name": "P60 - H2 capacity", "type": "range"},
            {"name": "P120 - H2 capacity", "type": "range"},
            {"name": "P60 - Load inc/dec time (hrs)", "type": "single"},
            {"name": "P120 - Load inc/dec time (hrs)", "type": "single"},
            {"name": "Conversion: H2 (1 Nm3/hr) to Coal (X ton/hr)", "type": "single"},
            {"name": "Conversion: H2 (X Nm3) to H2 (1 ton)", "type": "single"}
        ],
        "Dashboard": []
    }

    flaker_constraints = []
    for i in range(1, 5):
        flaker_constraints.extend([
            {"name": f"Flaker-{i} Load Capacity (TPD)", "type": "range"},
            {"name": f"Flaker-{i} H2 Specific Consumption (NM3/Ton)", "type": "single"},
            {"name": f"Flaker-{i} NG Specific Consumption (SCM/Ton)", "type": "single"},
        ])

    flaker_constraints.extend([{"name": "Flaker - Changeover time (NG to mix) (hrs)", "type": "single"},
                               {"name": "Flaker - H2 load inc/dec time (hrs)", "type": "single"}])
    ROLE_CONSTRAINTS["Flaker Plant"] = flaker_constraints
    return ROLE_CONSTRAINTS
