import datetime

import streamlit as st

from params import *
from utils.audit_logging import log_audit_entry, load_audit_log
from database import save_constraints


def constraint_entry_page():
    """Page for entering and managing constraints."""
    role = st.session_state.selected_role
    st.title(f"Constraint Entry for {role}")

    # Ensure role's constraints are initialized in session state
    if role not in st.session_state.constraint_values:
        st.session_state.constraint_values[role] = {
            constraint: {"min": 0, "max": 100} for constraint in ROLE_CONSTRAINTS.get(role, [])
        }

    st.write("### Enter Min/Max Constraints:")

    # Store proposed changes before confirmation
    if "proposed_changes" not in st.session_state:
        st.session_state.proposed_changes = {}

    changed_something = False

    # Create two columns for layout: input fields and audit log
    col1, col2 = st.columns([2, 1])

    with col1:
        for constraint_name in ROLE_CONSTRAINTS.get(role, []):
            current_min = st.session_state.constraint_values[role].get(constraint_name, {}).get("min", 0)
            current_max = st.session_state.constraint_values[role].get(constraint_name, {}).get("max", 100)

            st.subheader(f"Constraint: {constraint_name}")
            new_min = st.number_input(f"Min for {constraint_name}", value=current_min,
                                      key=f"{role}_{constraint_name}_min")
            new_max = st.number_input(f"Max for {constraint_name}", value=current_max,
                                      key=f"{role}_{constraint_name}_max")

            if new_min != current_min or new_max != current_max:
                st.session_state.proposed_changes[constraint_name] = {
                    "old_min": current_min, "new_min": new_min,
                    "old_max": current_max, "new_max": new_max
                }
                changed_something = True
                st.warning(f"Changes for {constraint_name} are pending confirmation.")

        if changed_something:
            st.write("---")
            st.write("### Confirm Changes:")
            if st.button("Confirm All Pending Changes"):
                for constraint_name, changes in st.session_state.proposed_changes.items():
                    old_min = changes["old_min"]
                    new_min = changes["new_min"]
                    old_max = changes["old_max"]
                    new_max = changes["new_max"]

                    # Update session state and log audit
                    if new_min != old_min:
                        log_audit_entry(st.session_state.username, role, f"{constraint_name} Min", old_min, new_min)
                        st.session_state.constraint_values[role][constraint_name]["min"] = new_min
                    if new_max != old_max:
                        log_audit_entry(st.session_state.username, role, f"{constraint_name} Max", old_max, new_max)
                        st.session_state.constraint_values[role][constraint_name]["max"] = new_max

                # # Round timestamp down to the minute for unique key
                # timestamp_key = datetime.datetime.now().replace(second=0, microsecond=0).isoformat()
                save_constraints(role, st.session_state.constraint_values[role])

                # # Store the entire set of constraints for the role at this timestamp
                # if role not in st.session_state.constraint_values:
                #     st.session_state.constraint_values[role] = {}
                #
                # # Ensure the current constraints are stored under the role's timestamped entry
                # current_constraints_for_role = {
                #     c_name: st.session_state.constraint_values[role].get(c_name, {"min": 0, "max": 100})
                #     for c_name in ROLE_CONSTRAINTS.get(role, [])
                # }
                #
                # if "history" not in st.session_state.constraint_values[role]:
                #     st.session_state.constraint_values[role]["history"] = {}
                #
                # st.session_state.constraint_values[role]["history"][timestamp_key] = current_constraints_for_role
                #
                # save_data(st.session_state.constraint_values, CONSTRAINT_DB_PATH)

                st.session_state.proposed_changes = {}  # Clear pending changes
                st.success("Constraints updated and audit log recorded!")
                st.rerun()  # Rerun to refresh the dashboard and clear warnings

    with col2:
        st.subheader("Audit Log (Last 10 entries)")
        audit_df = load_audit_log().tail(10)
        st.dataframe(audit_df, height=300, use_container_width=True)

    st.markdown("---")
    st.button("Go to Dashboard", on_click=lambda: st.session_state.update(current_page="dashboard"))
    st.button("Change Role",
              on_click=lambda: st.session_state.update(current_page="role_selection", selected_role=None))
