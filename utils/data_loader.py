# import json
# import os
#
#
# # --- Utility Functions (Simulated Database & Audit Log) ---
# def load_data(file_path, default_value={}):
#     """Loads data from a JSON file."""
#     if not os.path.exists(file_path):
#         return default_value
#     with open(file_path, "r") as f:
#         return json.load(f)
#
#
# def save_data(data, file_path):
#     """Saves data to a JSON file."""
#     with open(file_path, "w") as f:
#         json.dump(data, f, indent=4)
