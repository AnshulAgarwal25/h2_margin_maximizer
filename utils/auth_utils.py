import os
import uuid

import msal
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
WEBSITE_HOSTNAME = os.getenv("WEBSITE_HOSTNAME", "localhost:8501")
REDIRECT_URI = f"http://{WEBSITE_HOSTNAME}/" if "localhost" in WEBSITE_HOSTNAME else f"https://{WEBSITE_HOSTNAME}/"
SCOPE = ["User.Read", "GroupMember.Read.All"]
ALLOWED_GROUP_ID = os.getenv("AZURE_AD_GROUP_ID")


def get_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=None
    )


def build_auth_url():
    return get_msal_app().get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
        state=str(uuid.uuid4()),
        prompt="login"
    )


def acquire_token_from_code(code):
    return get_msal_app().acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )


def get_user_profile(access_token):
    graph_url = "https://graph.microsoft.com/v1.0/me"
    resp = requests.get(graph_url, headers={"Authorization": f"Bearer {access_token}"})
    return resp.json()


def check_group_membership(access_token):
    if not ALLOWED_GROUP_ID:
        return True
    group_url = "https://graph.microsoft.com/v1.0/me/memberOf"
    resp = requests.get(group_url, headers={"Authorization": f"Bearer {access_token}"})
    groups = resp.json().get("value", [])
    return any(g["id"] == ALLOWED_GROUP_ID for g in groups)


def handle_callback(code):
    token_response = acquire_token_from_code(code)
    if "access_token" not in token_response:
        return None
    access_token = token_response["access_token"]

    if not check_group_membership(access_token):
        return "unauthorized"

    user_info = get_user_profile(access_token)
    return {
        "access_token": access_token,
        "username": user_info.get("userPrincipalName", "unknown"),
        "full_name": user_info.get("displayName", "unknown")
    }


def is_authenticated(session_state):
    return session_state.get("authenticated", False)


def logout_user(session_state):
    for key in list(session_state.keys()):
        del session_state[key]
    logout_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/logout?post_logout_redirect_uri=http://{WEBSITE_HOSTNAME}/"
    st.markdown(f'<meta http-equiv="refresh" content="0;url={logout_url}">', unsafe_allow_html=True)
