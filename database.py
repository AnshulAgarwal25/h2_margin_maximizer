import datetime
import sqlite3

# --- Database Configuration ---
DB_FILE = 'hydrogen_allocation_tool.db'  # SQLite database file


# --- Utility for database connection ---
def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


# --- Table Creation Functions ---

def create_constraint_table(role_name, constraints):
    """
    Creates a dedicated table for a given role's constraints.
    Columns will be `timestamp` and each constraint name.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sanitize role name for table name (replace spaces and special chars)
    table_name = f"constraints_{role_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()}"

    # Build columns definition from constraint names
    # Using REAL for min/max values
    columns_sql = ", ".join(
        [f'"{c_name.replace(" ", "_")}_min" REAL, "{c_name.replace(" ", "_")}_max" REAL' for c_name in constraints])

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp TEXT PRIMARY KEY,
        {columns_sql}
    );
    """
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Table '{table_name}' ensured to exist.")
    except sqlite3.Error as e:
        print(f"Error creating table {table_name}: {e}")
    finally:
        conn.close()
    return table_name


def create_allocation_table(allocation_areas):
    """
    Creates the common allocation table.
    Columns will include timestamp, allocated, recommended, status, and comments for each area.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "allocations"

    # Build columns for allocated and recommended values
    data_columns_sql = ", ".join([
        f'"{area.replace(" ", "_").replace("-", "_")}_allocated" REAL, "{area.replace(" ", "_").replace("-", "_")}_recommended" REAL'
        for area in allocation_areas])

    # Build columns for status and comments
    status_comment_columns_sql = ", ".join([
        f'"{area.replace(" ", "_").replace("-", "_")}_status" TEXT, "{area.replace(" ", "_").replace("-", "_")}_comment" TEXT'
        for area in allocation_areas])

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp TEXT PRIMARY KEY,
        {data_columns_sql},
        {status_comment_columns_sql}
    );
    """
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Table '{table_name}' ensured to exist.")
    except sqlite3.Error as e:
        print(f"Error creating table {table_name}: {e}")
    finally:
        conn.close()
    return table_name


# --- Data Loading Functions ---

def load_latest_constraints(role_name, constraints_schema):
    """
    Loads the latest constraint entry for a given role.
    Returns a dictionary of current min/max values.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = f"constraints_{role_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()}"

    # Check if table exists (optional, as create_constraint_table handles it)
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if cursor.fetchone() is None:
        conn.close()
        return {c: {"min": 0, "max": 100} for c in constraints_schema}  # Return default if table doesn't exist

    try:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 1;")
        row = cursor.fetchone()
        if row:
            latest_constraints = {}
            for c_name in constraints_schema:
                col_name_min = f'"{c_name.replace(" ", "_")}_min"'
                col_name_max = f'"{c_name.replace(" ", "_")}_max"'
                latest_constraints[c_name] = {
                    "min": row[col_name_min.strip('"')] if col_name_min.strip('"') in row.keys() else 0,
                    # Access by key name after row_factory
                    "max": row[col_name_max.strip('"')] if col_name_max.strip('"') in row.keys() else 100
                }
            return latest_constraints
        else:
            return {c: {"min": 0, "max": 100} for c in constraints_schema}  # Return default if no data
    except sqlite3.Error as e:
        print(f"Error loading latest constraints for {role_name}: {e}")
        return {c: {"min": 0, "max": 100} for c in constraints_schema}  # Return default on error
    finally:
        conn.close()


def load_latest_allocation_data(allocation_data_schema):
    """
    Loads the latest hydrogen allocation data from the database.
    Returns a dictionary matching the HYDROGEN_ALLOCATION_DATA structure.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "allocations"

    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if cursor.fetchone() is None:
        conn.close()
        return allocation_data_schema  # Return default if table doesn't exist

    try:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 1;")
        row = cursor.fetchone()
        if row:
            latest_data = {}
            for area in allocation_data_schema.keys():
                area_clean = area.replace(" ", "_").replace("-", "_")
                latest_data[area] = {
                    "allocated": row[f"{area_clean}_allocated"] if f"{area_clean}_allocated" in row.keys() else 0,
                    "recommended": row[f"{area_clean}_recommended"] if f"{area_clean}_recommended" in row.keys() else 0,
                    "status": row[f"{area_clean}_status"] if f"{area_clean}_status" in row.keys() else "pending",
                    "comment": row[f"{area_clean}_comment"] if f"{area_clean}_comment" in row.keys() else ""
                }
            return latest_data
        else:
            return allocation_data_schema  # Return default if no data
    except sqlite3.Error as e:
        print(f"Error loading latest allocation data: {e}")
        return allocation_data_schema  # Return default on error
    finally:
        conn.close()


# --- Data Writing Functions ---

def save_constraints(role_name, constraint_values):
    """
    Saves a new timestamped entry of constraint values for a given role.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = f"constraints_{role_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()}"

    timestamp_key = datetime.datetime.now().replace(second=0, microsecond=0).isoformat()

    # Dynamically build column names and values for the insert statement
    columns = ["timestamp"]
    values = [timestamp_key]
    placeholders = ["?"]

    for c_name, data in constraint_values.items():
        col_name_min = f'"{c_name.replace(" ", "_")}_min"'
        col_name_max = f'"{c_name.replace(" ", "_")}_max"'
        columns.append(col_name_min)
        columns.append(col_name_max)
        values.append(data.get("min", 0))
        values.append(data.get("max", 100))
        placeholders.append("?")
        placeholders.append("?")

    columns_sql = ", ".join(columns)
    placeholders_sql = ", ".join(placeholders)

    insert_sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders_sql});"

    try:
        cursor.execute(insert_sql, values)
        conn.commit()
        print(f"Constraints for {role_name} saved successfully at {timestamp_key}.")
    except sqlite3.Error as e:
        print(f"Error saving constraints for {role_name}: {e}")
    finally:
        conn.close()


def save_allocation_data(allocation_data):
    """
    Saves a new timestamped entry of allocation data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "allocations"

    timestamp_key = datetime.datetime.now().replace(second=0, microsecond=0).isoformat()

    columns = ["timestamp"]
    values = [timestamp_key]
    placeholders = ["?"]

    for area, data in allocation_data.items():
        area_clean = area.replace(" ", "_").replace("-", "_")
        columns.append(f'"{area_clean}_allocated"')
        columns.append(f'"{area_clean}_recommended"')
        columns.append(f'"{area_clean}_status"')
        columns.append(f'"{area_clean}_comment"')

        values.append(data.get("allocated", 0))
        values.append(data.get("recommended", 0))
        values.append(data.get("status", "pending"))
        values.append(data.get("comment", ""))

        placeholders.extend(["?", "?", "?", "?"])

    columns_sql = ", ".join(columns)
    placeholders_sql = ", ".join(placeholders)

    insert_sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders_sql});"

    try:
        # Check if an entry for the current minute already exists to avoid PK violation
        cursor.execute(f"SELECT timestamp FROM {table_name} WHERE timestamp = ?;", (timestamp_key,))
        if cursor.fetchone():
            # If exists, update instead of insert (or handle as per requirement)
            print(f"Entry for {timestamp_key} already exists in allocations. Updating.")
            # For simplicity, if we hit this, it means a rapid change. We'll overwrite or skip.
            # A more robust system might update individual fields.
            # For now, let's just insert a new one by appending a microsecond or similar,
            # or allow multiple entries per minute if that's desired behavior.
            # For this exercise, we will just insert, allowing multiple entries per minute
            # if multiple updates occur very quickly within the same minute.
            # To strictly ensure unique key per minute, we'd need an UPDATE ON CONFLICT syntax.
            # SQLite doesn't have a direct UPSERT for this, but INSERT OR REPLACE could work.
            # However, INSERT OR REPLACE would replace the entire row, which might lose data
            # if we are tracking incremental changes.
            # For this case, we'll just insert as the PK is timestamp rounded to minute.
            # If multiple changes within a minute, they'll all be distinct entries for different seconds within that minute.
            # Let's adjust timestamp_key slightly to ensure uniqueness for rapid changes.
            timestamp_key = datetime.datetime.now().isoformat(timespec='seconds')  # Use seconds for better granularity
            columns[0] = "timestamp"  # Ensure timestamp column is still first
            values[0] = timestamp_key
            insert_sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders_sql});"  # Rebuild with new timestamp
            cursor.execute(insert_sql, values)
        else:
            cursor.execute(insert_sql, values)
        conn.commit()
        print(f"Allocation data saved successfully at {timestamp_key}.")
    except sqlite3.Error as e:
        print(f"Error saving allocation data: {e}")
    finally:
        conn.close()


# --- Initial Database Setup (Called once at app start) ---
def initialize_db(roles, role_constraints_map, allocation_areas):
    """
    Initializes the database by creating all necessary tables if they don't exist.
    """
    # Create constraint tables for each role
    for role in roles:
        create_constraint_table(role, role_constraints_map.get(role, []))
    # Create the common allocation table
    create_allocation_table(allocation_areas)

# --- Main execution for testing purposes (optional) ---
# if __name__ == "__main__":
#     # Dummy data for testing initialization
#     test_roles = ["Marketing", "H2 Plant"]
#     test_role_constraints = {
#         "Marketing": ["Budget Min", "Budget Max"],
#         "H2 Plant": ["H2 Purity Min", "H2 Pressure Max"]
#     }
#     test_allocation_areas = list({
#                                      "Pipeline": {}, "Bank": {}, "HCL": {}, "Flaker - 1": {}
#                                  }.keys())  # Use keys to get a list of areas
#
#     initialize_db(test_roles, test_role_constraints, test_allocation_areas)
#
#     # Example: Save some dummy constraints
#     dummy_marketing_constraints = {
#         "Budget Min": {"min": 1000, "max": 5000},
#         "Budget Max": {"min": 10000, "max": 50000}
#     }
#     save_constraints("Marketing", dummy_marketing_constraints)
#
#     # Example: Load latest constraints
#     latest_marketing_constraints = load_latest_constraints("Marketing", test_role_constraints["Marketing"])
#     print("\nLatest Marketing Constraints:", latest_marketing_constraints)
#
#     # Example: Save dummy allocation data
#     dummy_allocation_data = {
#         "Pipeline": {"allocated": 1500, "recommended": 1450, "status": "accepted", "comment": "Good"},
#         "Bank": {"allocated": 800, "recommended": 850, "status": "pending", "comment": ""},
#         "HCL": {"allocated": 300, "recommended": 320, "status": "rejected", "comment": "Too high"},
#         "Flaker - 1": {"allocated": 200, "recommended": 190, "status": "accepted", "comment": "Optimum"}
#     }
#     save_allocation_data(dummy_allocation_data)
#
#     # Example: Load latest allocation data
#     latest_allocation_data = load_latest_allocation_data(dummy_allocation_data)
#     print("\nLatest Allocation Data:", latest_allocation_data)
