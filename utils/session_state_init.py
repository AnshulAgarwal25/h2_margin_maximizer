import streamlit as st
from database import load_latest_allocation_data
from optimizer.run_optimizer import initial_db_trigger, last_run_constraints_trigger_run
from params import *


def session_state_init():
    # if "constraint_values" not in st.session_state:
    #     st.session_state.constraint_values = {}
    #
    # if "last_run_constraints" not in st.session_state:
    #     st.session_state.last_run_constraints = {}

    if "bank_filling_status" not in st.session_state:
        st.session_state.bank_filling_status = False
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

    # Initialize constraint_values as an empty dict to be populated on role selection
    if "constraint_values" not in st.session_state:
        st.session_state.constraint_values = {}

    # Load initial dashboard data from the database
    if "dashboard_data" not in st.session_state:
        st.session_state.dashboard_data = load_latest_allocation_data(HYDROGEN_ALLOCATION_DATA)

    # Flag to indicate if optimizer should run due to button click
    if "run_optimizer_button_clicked" not in st.session_state:
        st.session_state.run_optimizer_button_clicked = False

    if "optimizer_run" not in st.session_state:
        st.session_state.optimizer_run = False

    if "duration" not in st.session_state:
        st.session_state.duration = 0

    # --- OPTIMIZER TRIGGERING START ---
    if "last_run_constraints" not in st.session_state:
        last_run_constraints_trigger_run()
