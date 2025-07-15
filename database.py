import datetime
import json
import sqlite3

import pandas as pd
import pytz

# --- Database Configuration ---
DB_FILE = 'hydrogen_allocation_tool.db'  # SQLite database file


# --- Utility for database connection ---
def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


# --- Table Creation Functions ---

def create_constraint_table(role_name, constraints_schema):
    """
    Creates a dedicated table for a given role's constraints.
    Columns will be `timestamp` and columns derived from constraint_schema type.
    constraints_schema: List of dicts, e.g., [{"name": "Budget", "type": "range"}, {"name": "Limit", "type": "single"}]
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sanitize role name for table name (replace spaces and special chars)
    table_name = f"constraints_{role_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()}"

    columns_sql_parts = []
    for constraint in constraints_schema:
        c_name_clean = constraint["name"].replace(" ", "_").replace("-", "_")
        c_type = constraint["type"]
        if c_type == "range":
            columns_sql_parts.append(f'"{c_name_clean}_min" REAL')
            columns_sql_parts.append(f'"{c_name_clean}_max" REAL')
        elif c_type == "single":
            columns_sql_parts.append(f'"{c_name_clean}" REAL')  # Single value constraint
        # Add other types if needed in the future

    columns_sql = ", ".join(columns_sql_parts)

    if not columns_sql:
        print(f"Skipping table creation for '{table_name}' as no constraints are defined.")
        conn.close()
        return table_name  # Return early if no columns

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp TEXT PRIMARY KEY,
        {columns_sql}
    );
    """
    try:
        if table_name == 'constraints_dashboard':
            return 0
        cursor.execute(create_table_sql)
        conn.commit()
        # print(f"Table '{table_name}' ensured to exist.")
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

    # Build columns for min and max constraints & margin per unit
    constraints_columns_sql = ", ".join([
        f'"{area.replace(" ", "_").replace("-", "_")}_min_constrained" REAL, \
        "{area.replace(" ", "_").replace("-", "_")}_max_constrained" REAL, \
        "{area.replace(" ", "_").replace("-", "_")}_margin_per_unit" REAL'
        for area in allocation_areas])

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp TEXT PRIMARY KEY,
        {data_columns_sql},
        {status_comment_columns_sql},
        {constraints_columns_sql}
    );
    """
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        # print(f"Table '{table_name}' ensured to exist.")
    except sqlite3.Error as e:
        print(f"Error creating table {table_name}: {e}")
    finally:
        conn.close()
    return table_name


def create_optimizer_state_table():
    """
    Creates a table to store the last run constraints snapshot for the optimizer.
    This table will have a single row, updated periodically.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "optimizer_state"
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY DEFAULT 1, -- Use a default ID for a single row
        last_run_constraints_json TEXT,
        last_updated TEXT
    );
    """
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        # print(f"Table '{table_name}' ensured to exist.")
        # Ensure there's always at least one row for updates
        cursor.execute(
            f"INSERT OR IGNORE INTO {table_name} (id, last_run_constraints_json, last_updated) VALUES (1, ?, ?);",
            (json.dumps({}), datetime.datetime.now().isoformat()))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating table {table_name}: {e}")
    finally:
        conn.close()


# --- Data Loading Functions ---

def load_all_allocations():
    """
    Loads all entries from the 'allocations' table into a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing all allocation records,
                      or an empty DataFrame if the table doesn't exist or is empty.
    """
    conn = None
    try:
        conn = get_db_connection()

        # Check if the allocations table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allocations';")
        if cursor.fetchone() is None:
            print("Table 'allocations' does not exist. Returning empty DataFrame.")
            return pd.DataFrame()  # Return empty DataFrame if table doesn't exist

        # Load all data from the allocations table
        df = pd.read_sql_query("SELECT * FROM allocations ORDER BY timestamp ASC;", conn)
        print("Successfully loaded all allocations data.")
        return df
    except sqlite3.Error as e:
        print(f"Error loading all allocations data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    finally:
        if conn:
            conn.close()


def load_latest_constraints(role_name, constraints_schema):
    """
    Loads the latest constraint entry for a given role.
    Returns a dictionary of current values, respecting single/range types.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = f"constraints_{role_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()}"

    # Check if table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if cursor.fetchone() is None:
        conn.close()
        return {c["name"]: ({"min": 0, "max": 100} if c["type"] == "range" else 0) for c in constraints_schema}

    try:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 1;")
        row = cursor.fetchone()
        if row:
            latest_constraints = {}
            for constraint in constraints_schema:
                c_name = constraint["name"]
                c_name_clean = c_name.replace(" ", "_").replace("-", "_")
                c_type = constraint["type"]

                if c_type == "range":
                    col_name_min = f'"{c_name_clean}_min"'
                    col_name_max = f'"{c_name_clean}_max"'
                    latest_constraints[c_name] = {
                        "min": row[col_name_min.strip('"')] if col_name_min.strip('"') in row.keys() else 0,
                        "max": row[col_name_max.strip('"')] if col_name_max.strip('"') in row.keys() else 100
                    }
                elif c_type == "single":
                    col_name = f'"{c_name_clean}"'
                    latest_constraints[c_name] = row[col_name.strip('"')] if col_name.strip('"') in row.keys() else 0
            return latest_constraints
        else:
            # No data found, return default values based on schema
            return {c["name"]: ({"min": 0, "max": 100} if c["type"] == "range" else 0) for c in constraints_schema}
    except sqlite3.Error as e:
        print(f"Error loading latest constraints for {role_name}: {e}")
        return {c["name"]: ({"min": 0, "max": 100} if c["type"] == "range" else 0) for c in constraints_schema}
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
                    "comment": row[f"{area_clean}_comment"] if f"{area_clean}_comment" in row.keys() else "",
                    "min_constrained": row[
                        f"{area_clean}_min_constrained"] if f"{area_clean}_min_constrained" in row.keys() else 0,
                    "max_constrained": row[
                        f"{area_clean}_max_constrained"] if f"{area_clean}_max_constrained" in row.keys() else 0,
                    "margin_per_unit": row[
                        f"{area_clean}_margin_per_unit"] if f"{area_clean}_margin_per_unit" in row.keys() else 0,
                }
            return latest_data
        else:
            return allocation_data_schema  # Return default if no data
    except sqlite3.Error as e:
        print(f"Error loading latest allocation data: {e}")
        return allocation_data_schema  # Return default on error
    finally:
        conn.close()


def load_optimizer_last_run_constraints():
    """
    Loads the last run constraints snapshot from the optimizer_state table.
    Returns an empty dictionary if no data is found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "optimizer_state"
    try:
        cursor.execute(f"SELECT last_run_constraints_json FROM {table_name} WHERE id = 1;")
        result = cursor.fetchone()
        if result and result['last_run_constraints_json']:
            return json.loads(result['last_run_constraints_json'])
        else:
            return {}  # Return empty dict if no data or JSON is empty
    except sqlite3.Error as e:
        print(f"Error loading optimizer state: {e}")
        return {}  # Return empty dict on error
    finally:
        conn.close()


# --- Data Writing Functions ---

def save_constraints(role_name, current_constraint_values, constraints_schema):
    """
    Saves a new timestamped entry of constraint values for a given role,
    handling single vs. range types.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = f"constraints_{role_name.replace(' ', '_').replace('-', '_').replace('.', '_').lower()}"

    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if cursor.fetchone() is None:
        print(f"Table '{table_name}' does not exist. Skipping constraint save.")
        conn.close()
        return  # Exit if table does not exist

    ist = pytz.timezone('Asia/Kolkata')
    timestamp_key = datetime.datetime.now(ist).isoformat(timespec='milliseconds')

    columns = ["timestamp"]
    values = [timestamp_key]
    placeholders = ["?"]

    for constraint in constraints_schema:
        c_name = constraint["name"]
        c_name_clean = c_name.replace(" ", "_").replace("-", "_")
        c_type = constraint["type"]

        if c_type == "range":
            # Expecting current_constraint_values[c_name] to be a dict like {"min": X, "max": Y}
            columns.append(f'"{c_name_clean}_min"')
            columns.append(f'"{c_name_clean}_max"')
            values.append(current_constraint_values.get(c_name, {}).get("min", 0))
            values.append(current_constraint_values.get(c_name, {}).get("max", 100))
            placeholders.extend(["?", "?"])
        elif c_type == "single":
            # Expecting current_constraint_values[c_name] to be a single value
            columns.append(f'"{c_name_clean}"')
            values.append(current_constraint_values.get(c_name, 0))
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
    allocation_data.pop("caustic", None)  # dropping keys which are not required to be saved

    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "allocations"

    ist = pytz.timezone('Asia/Kolkata')
    timestamp_key = datetime.datetime.now(ist).isoformat(timespec='milliseconds')

    columns = ["timestamp"]
    values = [timestamp_key]
    placeholders = ["?"]

    for area, data in allocation_data.items():
        area_clean = area.replace(" ", "_").replace("-", "_")
        columns.append(f'"{area_clean}_allocated"')
        columns.append(f'"{area_clean}_recommended"')
        columns.append(f'"{area_clean}_status"')
        columns.append(f'"{area_clean}_comment"')
        columns.append(f'"{area_clean}_min_constrained"')
        columns.append(f'"{area_clean}_max_constrained"')
        columns.append(f'"{area_clean}_margin_per_unit"')

        values.append(data.get("allocated", 0))
        values.append(data.get("recommended", 0))
        values.append(data.get("status", "pending"))
        values.append(data.get("comment", ""))
        values.append(data.get("min_constrained", 0))
        values.append(data.get("max_constrained", 0))
        values.append(data.get("margin_per_unit", 0))

        placeholders.extend(["?", "?", "?", "?", "?", "?", "?"])

    columns_sql = ", ".join(columns)
    placeholders_sql = ", ".join(placeholders)

    insert_sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders_sql});"

    try:
        cursor.execute(insert_sql, values)
        conn.commit()
        print(f"Allocation data saved successfully at {timestamp_key}.")
    except sqlite3.Error as e:
        print(f"Error saving allocation data: {e}")
    finally:
        conn.close()


def save_optimizer_last_run_constraints(constraints_snapshot):
    """
    Saves the current constraints snapshot to the optimizer_state table.
    This will update the single row in this table.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = "optimizer_state"
    constraints_json = json.dumps(constraints_snapshot)

    ist = pytz.timezone('Asia/Kolkata')
    last_updated = datetime.datetime.now(ist).isoformat(timespec='milliseconds')

    update_sql = f"""
    INSERT OR REPLACE INTO {table_name} (id, last_run_constraints_json, last_updated)
    VALUES (1, ?, ?);
    """
    try:
        cursor.execute(update_sql, (constraints_json, last_updated))
        conn.commit()
        print(f"Optimizer state (last_run_constraints) saved successfully at {last_updated}.")
    except sqlite3.Error as e:
        print(f"Error saving optimizer state: {e}")
    finally:
        conn.close()


# --- Initial Database Setup (Called once at app start) ---
def initialize_db(roles, role_constraints_map, allocation_areas):
    """
    Initializes the database by creating all necessary tables if they don't exist.
    """
    # Create constraint tables for each role
    for role in roles:
        constraints_schema = role_constraints_map.get(role, [])
        if constraints_schema:  # Only attempt to create if constraints are defined
            create_constraint_table(role, constraints_schema)
    # Create the common allocation table
    create_allocation_table(allocation_areas)
    create_optimizer_state_table()
