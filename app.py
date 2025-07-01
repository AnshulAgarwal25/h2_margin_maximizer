# app.py
import time
import warnings
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from database import (
    initialize_db,
    load_latest_allocation_data,
    load_latest_constraints
)
from optimizer.run_optimizer import trigger_optimizer_if_needed, last_run_constraints_trigger_run, initial_db_trigger
from pages.auth import auth_page
from pages.common_dashboard import common_dashboard_page
from pages.constraint_entry import constraint_entry_page
from params import *

st.set_page_config(layout="wide", page_title="Hydrogen Allocation Tool",
                   initial_sidebar_state="collapsed", page_icon="📈")

warnings.filterwarnings("ignore", category=DeprecationWarning)
initialize_db(ROLES, get_constraints(), list(HYDROGEN_ALLOCATION_DATA.keys()))

# --- Session State Initialization ---
if "initial_db_setup_done" not in st.session_state:
    initial_db_trigger()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = "Guest"  # Simulated user
if "selected_role" not in st.session_state:
    st.session_state.selected_role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "auth"

# Load initial dashboard data from the database
if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = load_latest_allocation_data(HYDROGEN_ALLOCATION_DATA)

# Initialize constraint_values as an empty dict to be populated on role selection
if "constraint_values" not in st.session_state:
    st.session_state.constraint_values = {}

# --- OPTIMIZER TRIGGERING START ---
if "last_run_constraints" not in st.session_state:
    last_run_constraints_trigger_run()

# Flag to indicate if optimizer should run due to button click
if "run_optimizer_button_clicked" not in st.session_state:
    st.session_state.run_optimizer_button_clicked = False

if "optimizer_run" not in st.session_state:
    st.session_state.optimizer_run = False


def main():
    # Display current page based on session state
    if st.session_state.current_page != "dashboard":
        st.session_state.optimizer_triggered_in_current_run = False

    if st.session_state.current_page == "auth":
        auth_page()
    elif st.session_state.current_page == "role_selection":
        auth_page()
    elif st.session_state.current_page == "constraint_entry":
        if st.session_state.selected_role and st.session_state.selected_role != "Dashboard":
            constraint_entry_page()
        else:
            st.warning("No role selected for constraint entry or selected role is 'Dashboard'.")
            st.session_state.current_page = "role_selection"
            st.rerun()
    elif st.session_state.current_page == "dashboard":
        if "first_dashboard_load" not in st.session_state:
            st.session_state.first_dashboard_load = True
            ROLE_CONSTRAINTS = get_constraints()
            for role_name in ROLES:
                if role_name in ROLE_CONSTRAINTS:
                    st.session_state.constraint_values[role_name] = load_latest_constraints(role_name,
                                                                                            ROLE_CONSTRAINTS[
                                                                                                role_name])
        trigger_optimizer_if_needed()
        common_dashboard_page()


refresh_interval_ms = 5 * 60 * 1000  # 3 minutes in milliseconds
st_autorefresh(interval=refresh_interval_ms, key="autorefresh_timer")
print(f"---Refreshed---{datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y %H:%M:%S')}")
main()
