# app.py

import streamlit as st

from database import (
    initialize_db,
    load_latest_allocation_data
)
from pages.auth import auth_page
from pages.common_dashboard import common_dashboard_page
from pages.constraint_entry import constraint_entry_page
from params import *

# from utils.data_loader import load_data

initialize_db(ROLES, ROLE_CONSTRAINTS, list(HYDROGEN_ALLOCATION_DATA.keys()))

# --- Session State Initialization ---

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = "Guest"  # Simulated user
if "selected_role" not in st.session_state:
    st.session_state.selected_role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"
# if "constraint_values" not in st.session_state:
#     st.session_state.constraint_values = load_data(CONSTRAINT_DB_PATH)
# if "dashboard_data" not in st.session_state:
#     st.session_state.dashboard_data = HYDROGEN_ALLOCATION_DATA

if "constraint_values" not in st.session_state:
    st.session_state.constraint_values = {}
    # Initialize empty, will load per role

# Load initial dashboard data from the database
if "dashboard_data" not in st.session_state:
    # Use load_latest_allocation_data from db_manager.py
    st.session_state.dashboard_data = load_latest_allocation_data(HYDROGEN_ALLOCATION_DATA)


# --- Main Application Logic ---

def main():
    st.set_page_config(layout="centered",
                       page_title="Hydrogen Allocation Tool")  # Adjusted to centered for better general UI

    # Display current page based on session state
    if st.session_state.current_page == "auth":
        auth_page()
    elif st.session_state.current_page == "role_selection":
        # After successful login, user is redirected to role selection
        # This is essentially the auth_page without the initial login prompt
        auth_page()
    elif st.session_state.current_page == "constraint_entry":
        if st.session_state.selected_role:
            constraint_entry_page()
        else:
            st.warning("No role selected. Please select a role first.")
            st.session_state.current_page = "role_selection"
            st.rerun()
    elif st.session_state.current_page == "dashboard":
        common_dashboard_page()


if __name__ == "__main__":
    main()
