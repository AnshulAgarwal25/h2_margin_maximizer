import pandas as pd
import streamlit as st

from database import save_allocation_data
from optimizer.run_optimizer import trigger_optimizer_if_needed
from utils.downloader import downloader_allocation, downloader_audit


@st.dialog("New Recommendation Available")
def optimizer_run_notification():
    st.write("Optimizer ran. New Recommendation Available!")


def common_dashboard_page():
    """Displays the common hydrogen allocation dashboard."""
    st.title("Hydrogen Allocation Dashboard (NM³/hr)")
    st.write(f"Logged in as: **{st.session_state.username}** (Role: **{st.session_state.selected_role}**)")

    if st.session_state.optimizer_run:
        optimizer_run_notification()
        st.session_state.optimizer_run = False

    st.write("### Current Hydrogen Allocations:")

    # Convert dashboard data to a DataFrame for easy display
    df = pd.DataFrame([
        {"Area": area,
         "Allocated (NM³/hr)": data["allocated"],
         "Recommended (NM³/hr)": data["recommended"],
         "Status": data["status"],
         "Comments": data["comment"],
         "Min (Constrained)": data['min_constrained'],
         "Max (Constrained)": data['max_constrained']}
        for area, data in st.session_state.dashboard_data.items()
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    total_df = pd.DataFrame([{'Current Flow (H2 in NM3/hr)': df["Allocated (NM³/hr)"].sum(),
                              'Recommended Flow (H2 in NM3/hr)': df["Recommended (NM³/hr)"].sum()}])
    st.dataframe(total_df, use_container_width=False, hide_index=True)

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
            status_radio = st.radio(f"Action for {area}", ["Accept", "Reject"],
                                    index=0 if current_status == "accepted" else (
                                        1 if current_status == "rejected" else 0),
                                    key=f"action_{area}")

            if status_radio == "Accept":
                new_status = "accepted"
            elif status_radio == "Reject":
                new_status = "rejected"
            else:
                new_status = "pending"

            if new_status != current_status:
                st.session_state.dashboard_data[area]["status"] = new_status
                save_allocation_data(st.session_state.dashboard_data)
                st.success(f"Status for {area} changed to {new_status}!")

        with col_comment:
            current_comment = data["comment"]
            new_comment = st.text_input(f"Comments for {area}", value=current_comment, key=f"comment_{area}")
            if new_comment != current_comment:
                st.session_state.dashboard_data[area]["comment"] = new_comment
                save_allocation_data(st.session_state.dashboard_data)
                st.success(f"Comment for {area} updated!")

    st.markdown("---")
    if st.session_state.selected_role != "Dashboard":
        st.button("Go to Constraint Entry", on_click=lambda: st.session_state.update(current_page="constraint_entry"))

    if st.button("Run Optimizer"):
        st.session_state.run_optimizer_button_clicked = True
        trigger_optimizer_if_needed(manual_trigger=True)

    st.button("Change Role",
              on_click=lambda: st.session_state.update(current_page="role_selection", selected_role=None))

    downloader_allocation()
    downloader_audit()
