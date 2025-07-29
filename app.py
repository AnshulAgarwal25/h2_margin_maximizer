# app.py
import time
import warnings
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from database import (
    initialize_db,
    load_latest_constraints
)
from optimizer.run_optimizer import trigger_optimizer_if_needed
from pages_files.auth import auth_page
from pages_files.common_dashboard import common_dashboard_page
from pages_files.constraint_entry import constraint_entry_page
from pages_files.optimizer_run_latest_values import display_latest_values
from params import *
from utils.audit_logging import initialize_audit_log_table
from utils.session_state_init import session_state_init

st.set_page_config(layout="wide", page_title="Hydrogen Allocation Tool",
                   initial_sidebar_state="collapsed", page_icon="📈")

warnings.filterwarnings("ignore", category=DeprecationWarning)
initialize_db(ROLES, get_constraints(), list(HYDROGEN_ALLOCATION_DATA.keys()))
initialize_audit_log_table()

session_state_init()


def main():
    # Display the current page based on session state
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
            role_constraints = get_constraints()
            for role_name in ROLES:
                if role_name in role_constraints:
                    st.session_state.constraint_values[role_name] = load_latest_constraints(role_name,
                                                                                            role_constraints[
                                                                                                role_name])
        trigger_optimizer_if_needed()
        common_dashboard_page()
    elif st.session_state.current_page == "optimizer_backend_values":
        display_latest_values()


refresh_interval_ms = 4 * 60 * 1000  # 3 minutes in milliseconds
st_autorefresh(interval=refresh_interval_ms, key="autorefresh_timer")
print(f"---Refreshed---{datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y %H:%M:%S')}")
main()
