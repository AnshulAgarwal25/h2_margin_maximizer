import streamlit as st


def display_latest_values():
    st.title("🧮 Latest Optimizer Backend Values")

    dcs_constraints = st.session_state.get("dcs_constraints", 0)
    current_flow = st.session_state.get("current_flow", 0)
    constraints = st.session_state.get("user_input_constraints", 0)
    dcs_raw_data = st.session_state.get("dcs_raw_data", 0)

    # User Input Constraints
    st.subheader("🔸 User Input Constraints")
    st.write(constraints)

    col1, col2 = st.columns([2, 2])
    with col1:
        st.subheader("🔹 DCS Constraints")
        st.dataframe(dcs_constraints)

    with col2:
        st.subheader("🔸 Current Flow")
        st.dataframe(current_flow)

    st.subheader("🔸 Raw DCS Data Dump")
    st.dataframe(dcs_raw_data)
    st.button("Go to Dashboard", on_click=lambda: st.session_state.update(current_page="dashboard"))
