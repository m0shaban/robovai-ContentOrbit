"""
ContentOrbit Enterprise - Dashboard Authentication
==================================================
Simple password-based authentication for dashboard access.
"""

import streamlit as st
import hashlib
from typing import Optional


def hash_password(password: str) -> str:
    """Hash password for comparison"""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(correct_password: str) -> bool:
    """
    Check if user has entered correct password.
    Returns True if authenticated.
    """

    def password_entered():
        """Checks whether password entered is correct"""
        entered = st.session_state.get("password", "")
        st.session_state["login_attempted"] = True
        if entered == correct_password:
            st.session_state["authenticated"] = True
            st.session_state["login_error"] = False
            # Don't store password
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False
            st.session_state["login_error"] = True

    # First run or not authenticated
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "login_attempted" not in st.session_state:
        st.session_state["login_attempted"] = False
    if "login_error" not in st.session_state:
        st.session_state["login_error"] = False

    # Already authenticated
    if st.session_state["authenticated"]:
        return True

    # Show login form
    st.markdown(
        """
    <div style="
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    ">
        <h1 style="color: #667eea; margin-bottom: 0.5rem;">🚀 ContentOrbit</h1>
        <p style="color: #718096; margin-bottom: 2rem;">Enterprise Dashboard</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.text_input(
            "🔐 Enter Password",
            type="password",
            key="password",
            on_change=password_entered,
            placeholder="Dashboard password...",
        )

        # Only show error after an actual failed attempt
        if st.session_state.get("login_attempted") and st.session_state.get("login_error"):
            st.error("❌ Incorrect password. Please try again.")

    return False


def logout():
    """Log out the user"""
    st.session_state["authenticated"] = False
    if "login_attempted" in st.session_state:
        del st.session_state["login_attempted"]
    if "login_error" in st.session_state:
        del st.session_state["login_error"]


def render_logout_button():
    """Render logout button in sidebar"""
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()
