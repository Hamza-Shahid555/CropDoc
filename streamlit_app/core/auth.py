"""Lightweight sqlite + bcrypt auth. No external OAuth dependency — this is a
single-deployment FYP demo app, not a multi-tenant SaaS, so a self-contained
username/password store is the right amount of engineering."""

import bcrypt
import streamlit as st

from . import db

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def ensure_demo_user() -> None:
    if not db.get_user_by_username(DEMO_USERNAME):
        db.create_user(DEMO_USERNAME, _hash_password(DEMO_PASSWORD))


def register(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if db.get_user_by_username(username):
        return False, "That username is already taken."
    db.create_user(username, _hash_password(password))
    return True, "Account created — you can log in now."


def login(username: str, password: str) -> tuple[bool, str]:
    user = db.get_user_by_username(username.strip())
    if not user or not _verify_password(password, user["password_hash"]):
        return False, "Invalid username or password."
    st.session_state["user"] = {"id": user["id"], "username": user["username"]}
    return True, "Logged in."


def logout() -> None:
    for key in ("user", "active_session_id", "messages"):
        st.session_state.pop(key, None)


def current_user() -> dict | None:
    return st.session_state.get("user")


def require_login() -> dict:
    """Render a login/register form and st.stop() the page until authenticated."""
    user = current_user()
    if user:
        return user

    st.markdown(
        "<div class='auth-hero'><h1>🌿 CropDoc</h1>"
        "<p>AI-powered crop disease diagnosis and advisory platform</p></div>",
        unsafe_allow_html=True,
    )
    tab_login, tab_register = st.tabs(["Log in", "Create account"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", value="demo")
            password = st.text_input("Password", type="password", value="demo1234")
            submitted = st.form_submit_button("Log in", width="stretch")
        if submitted:
            ok, msg = login(username, password)
            if ok:
                st.rerun()
            else:
                st.error(msg)
        st.caption("Demo account is pre-filled: **demo** / **demo1234**")

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            submitted_r = st.form_submit_button("Create account", width="stretch")
        if submitted_r:
            ok, msg = register(new_username, new_password)
            (st.success if ok else st.error)(msg)

    st.stop()
