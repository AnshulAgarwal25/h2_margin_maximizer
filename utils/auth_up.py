import streamlit as st

from utils.auth_utils import build_auth_url, handle_callback, is_authenticated


def engage_auth_page():
    # Read query params
    query_params = st.experimental_get_query_params()
    code = query_params.get("code", [None])[0]
    error = query_params.get("error", [None])[0]

    # Process authentication callback
    if code and not st.session_state.get("access_token"):
        result = handle_callback(code)

        if result == "unauthorized":
            st.experimental_set_query_params(error="unauthorized")
            st.session_state.authenticated = False
            st.rerun()
        elif result:
            st.session_state.username = st.session_state['username']
            st.session_state.update(result)
            st.session_state.authenticated = True
            st.experimental_set_query_params()
            st.session_state.current_page = "role_selection"
            st.rerun()
        else:
            st.error("Authentication failed.")
            st.session_state.authenticated = False
            st.stop()

    if error == "unauthorized":
        st.error("❌ You are not authorized to use this app.")

    if not is_authenticated(st.session_state):
        st.info("Please log in with your Microsoft account.")
        if st.button("🔐 Login with Microsoft"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={build_auth_url()}">', unsafe_allow_html=True)
    else:
        st.success(f"Welcome, **{st.session_state['full_name']}**!")
        st.write(f"👤 **Username**: `{st.session_state['username']}`")
        st.write(f"🧑‍💼 **Full Name**: `{st.session_state['full_name']}`")
        st.session_state.current_page = "role_selection"
        st.session_state.username = st.session_state['username']

        # if st.button("🚪 Logout"):
        #     logout_user(st.session_state)
        #     st.stop()
