import pandas as pd
import streamlit as st

from database import save_allocation_data


def common_dashboard_page():
    """Displays the common hydrogen allocation dashboard."""
    st.title("Common Hydrogen Allocation Dashboard (NM³/hr)")
    st.write(f"Logged in as: **{st.session_state.username}** (Role: **{st.session_state.selected_role}**)")

    st.write("### Current Hydrogen Allocations:")

    # Convert dashboard data to a DataFrame for easy display
    df = pd.DataFrame([
        {"Area": area,
         "Allocated (NM³/hr)": data["allocated"],
         "Recommended (NM³/hr)": data["recommended"],
         "Status": data["status"],
         "Comments": data["comment"]}
        for area, data in st.session_state.dashboard_data.items()
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.write("---")
    st.write("### Operator Actions (Accept/Reject Recommendations):")

    # Dynamic UI for accepting/rejecting recommendations
    for area, data in st.session_state.dashboard_data.items():
        st.subheader(f"Area: {area}")
        col_rec, col_action, col_comment = st.columns([1, 1, 3])

        with col_rec:
            st.metric(label="Recommended", value=data["recommended"])
        with col_action:
            current_status = data["status"]
            if current_status == "accepted":
                st.success("Accepted")
                status_radio = st.radio(f"Action for {area}", ["Accept", "Reject"], index=0, key=f"action_{area}")
            elif current_status == "rejected":
                st.error("Rejected")
                status_radio = st.radio(f"Action for {area}", ["Accept", "Reject"], index=1, key=f"action_{area}")
            else:
                status_radio = st.radio(f"Action for {area}", ["Accept", "Reject"], index=0,
                                        key=f"action_{area}")  # Default to Accept

            new_status = ""
            if status_radio == "Accept":
                new_status = "accepted"
            elif status_radio == "Reject":
                new_status = "rejected"
            else:
                new_status = "pending"

            if new_status != current_status:
                st.session_state.dashboard_data[area]["status"] = new_status
                save_allocation_data(st.session_state.dashboard_data)
                # No audit log for status change as it's operator action, not constraint change
                st.success(f"Status for {area} changed to {new_status}!")
                st.rerun()

        with col_comment:
            current_comment = data["comment"]
            new_comment = st.text_input(f"Comments for {area}", value=current_comment, key=f"comment_{area}")
            if new_comment != current_comment:
                st.session_state.dashboard_data[area]["comment"] = new_comment
                save_allocation_data(st.session_state.dashboard_data)
                # No audit log for comment change as it's operator action, not constraint change
                st.success(f"Comment for {area} updated!")
                st.rerun()

    st.markdown("---")
    st.button("Go to Constraint Entry", on_click=lambda: st.session_state.update(current_page="constraint_entry"))
    st.button("Change Role",
              on_click=lambda: st.session_state.update(current_page="role_selection", selected_role=None))
