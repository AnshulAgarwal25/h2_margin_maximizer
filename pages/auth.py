import streamlit as st

from database import load_latest_constraints
from params import *
from utils.auth_up import engage_auth_page


def auth_page():
    """Simulated authentication and role selection page."""
    st.title("Hydrogen Allocation Tool - Login")
    st.write("### Welcome! Please select your role to proceed.")

    # Simulate user ID for demonstration
    if not st.session_state.authenticated:
        # engage_auth_page()

        # Bypass Microsoft Login for Testing and Simulation
        st.session_state.username = st.text_input("Enter your User ID (e.g., 'user123')", value="user123")
        if st.button("Simulate Login"):
            st.session_state.authenticated = True
            st.session_state.current_page = "role_selection"
            st.rerun()

    if st.session_state.authenticated:
        st.write(f"Logged in as: **{st.session_state.username}**")
        selected_role = st.selectbox("Select your role:", [""] + ROLES, index=0)

        if selected_role:
            st.session_state.selected_role = selected_role
            if selected_role == "Dashboard":  # New condition for Dashboard role
                st.session_state.current_page = "dashboard"
            else:
                # Load the latest constraints for the newly selected role (only if not Dashboard)
                ROLE_CONSTRAINTS = get_constraints()
                st.session_state.constraint_values[selected_role] = load_latest_constraints(
                    selected_role,
                    ROLE_CONSTRAINTS.get(selected_role, [])
                )
                st.session_state.current_page = "constraint_entry"
            st.rerun()
        else:
            st.info("Please select a role to continue.")
