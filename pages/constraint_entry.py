import streamlit as st

from database import load_latest_constraints
from database import save_constraints
from optimizer.run_optimizer import trigger_optimizer_if_needed
from params import *
from utils.audit_logging import log_audit_entry, load_audit_log


def constraint_entry_page():
    ROLE_CONSTRAINTS = get_constraints()
    """Page for entering and managing constraints."""
    role = st.session_state.selected_role
    st.title(f"Constraint Entry for {role}")

    # Ensure role's constraints are initialized in session state (should be loaded from DB on role selection)
    if role not in st.session_state.constraint_values:
        st.session_state.constraint_values[role] = load_latest_constraints(
            role,
            ROLE_CONSTRAINTS.get(role, [])
        )

    st.write("### Enter Constraints:")

    # Store proposed changes before confirmation
    if "proposed_changes" not in st.session_state:
        st.session_state.proposed_changes = {}

    changed_something = False

    col1, col2 = st.columns([2, 1])
    with col1:
        for constraint_item in ROLE_CONSTRAINTS.get(role, []):
            constraint_name = constraint_item["name"]
            constraint_type = constraint_item["type"]

            st.subheader(f"Constraint: {constraint_name}")

            if constraint_type == "range":
                current_min = st.session_state.constraint_values[role].get(constraint_name, {}).get("min", 0)
                current_max = st.session_state.constraint_values[role].get(constraint_name, {}).get("max", 100)

                constraint_disabled = constraint_item.get("disabled", False)

                new_min = st.number_input(f"Min for {constraint_name}", value=current_min,
                                          key=f"{role}_{constraint_name}_min", disabled=constraint_disabled)
                new_max = st.number_input(f"Max for {constraint_name}", value=current_max,
                                          key=f"{role}_{constraint_name}_max", disabled=constraint_disabled)

                if not constraint_disabled and (new_min != current_min or new_max != current_max):
                    st.session_state.proposed_changes[constraint_name] = {
                        "old_min": current_min, "new_min": new_min,
                        "old_max": current_max, "new_max": new_max,
                        "type": "range"
                    }
                    changed_something = True
                    st.warning(f"Changes for {constraint_name} are pending confirmation.")

            elif constraint_type == "single":
                current_value = st.session_state.constraint_values[role].get(constraint_name, 0)

                constraint_disabled = constraint_item.get("disabled", False)
                new_value = st.number_input(f"Value for {constraint_name}", value=current_value,
                                            key=f"{role}_{constraint_name}_single", disabled=constraint_disabled)

                if not constraint_disabled and new_value != current_value:
                    st.session_state.proposed_changes[constraint_name] = {
                        "old_value": current_value, "new_value": new_value,
                        "type": "single"
                    }
                    changed_something = True
                    st.warning(f"Changes for {constraint_name} are pending confirmation.")

        if changed_something:
            st.write("---")
            st.write("### Confirm Changes:")
            if st.button("Confirm All Pending Changes"):
                for constraint_name, changes in st.session_state.proposed_changes.items():
                    constraint_type = changes["type"]
                    if constraint_type == "range":
                        old_min = changes["old_min"]
                        new_min = changes["new_min"]
                        old_max = changes["old_max"]
                        new_max = changes["new_max"]

                        if new_min != old_min:
                            log_audit_entry(st.session_state.username, role, f"{constraint_name} Min", old_min, new_min)
                            st.session_state.constraint_values[role][constraint_name]["min"] = new_min
                        if new_max != old_max:
                            log_audit_entry(st.session_state.username, role, f"{constraint_name} Max", old_max, new_max)
                            st.session_state.constraint_values[role][constraint_name]["max"] = new_max
                    elif constraint_type == "single":
                        old_value = changes["old_value"]
                        new_value = changes["new_value"]
                        if new_value != old_value:
                            log_audit_entry(st.session_state.username, role, constraint_name, old_value, new_value)
                            st.session_state.constraint_values[role][constraint_name] = new_value

                save_constraints(role, st.session_state.constraint_values[role], ROLE_CONSTRAINTS.get(role, []))
                st.session_state.proposed_changes = {}  # Clear pending changes
                st.success("Constraints updated and audit log recorded!")

                trigger_optimizer_if_needed()
                st.rerun()  # Rerun to refresh the dashboard and clear warnings

    with col2:
        st.subheader("Audit Log (Last 10 entries)")
        audit_df = load_audit_log().tail(10)
        st.dataframe(audit_df, height=300, use_container_width=True)

    st.markdown("---")
    st.button("Go to Dashboard", on_click=lambda: st.session_state.update(current_page="dashboard"))
    st.button("Change Role",
              on_click=lambda: st.session_state.update(current_page="role_selection", selected_role=None))
