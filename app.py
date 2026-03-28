"""
AI Mock Interview Platform
Main Streamlit application with interview functionality.
"""

import html
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

ADMIN_USERS = {"test10", "admin", "umar"}


def is_admin_user(username: str) -> bool:
    return (username or "").strip().lower() in {u.lower() for u in ADMIN_USERS}

from config import SENIORITY_LEVELS, TOTAL_QUESTIONS
from utils.db import (
    create_session,
    get_session,
    delete_session,
    init_db,
    create_user,
    verify_user,
    save_interview,
    get_user_interviews,
    get_all_interviews_admin,
    get_all_users_admin,
)
from utils.interview_engine import (
    get_first_question,
    evaluate_answer_and_get_next,
    generate_final_report,
)
from utils.pdf_parser import parse_document
from utils.voice import speech_to_text, text_to_speech


def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-main: #f4f5fb;
        --bg-soft: #eef0f8;
        --panel: rgba(255, 255, 255, 0.72);
        --panel-strong: rgba(255, 255, 255, 0.88);
        --panel-sidebar: linear-gradient(180deg, #f3f4fb 0%, #eceef8 100%);
        --border: rgba(123, 132, 176, 0.18);
        --border-strong: rgba(107, 123, 204, 0.28);
        --text-primary: #2c3353;
        --text-secondary: #677095;
        --text-soft: #8b92b2;
        --primary: #6f86ff;
        --primary-2: #8a7dff;
        --primary-3: #5e74ee;
        --accent: #a99cff;
        --success: #3bb273;
        --warning: #ffbf47;
        --danger: #ff6b6b;
        --shadow-soft: 0 10px 30px rgba(93, 104, 150, 0.10);
        --shadow-card: 0 12px 34px rgba(98, 109, 153, 0.12);
        --shadow-hover: 0 16px 38px rgba(98, 109, 153, 0.16);
        --radius-xl: 24px;
        --radius-lg: 18px;
        --radius-md: 14px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(152, 162, 255, 0.10), transparent 30%),
            radial-gradient(circle at top right, rgba(192, 181, 255, 0.10), transparent 28%),
            linear-gradient(180deg, #f8f9fd 0%, #f3f5fb 35%, #eef1f8 100%);
        color: var(--text-primary);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
        background: var(--panel-sidebar);
        border-right: 1px solid rgba(122, 132, 176, 0.14);
        box-shadow: 4px 0 28px rgba(110, 120, 166, 0.06);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.4rem;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    h1 {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-size: 3rem !important;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem !important;
    }

    h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    p, li, label, .stMarkdown, .stCaption {
        color: var(--text-secondary);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: rgba(255,255,255,0.55);
        border-radius: 14px;
        padding: 4px;
        border: 1px solid rgba(123,132,176,0.14);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
    }

    .stTabs [data-baseweb="tab-list"] button {
        flex: 1;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        color: var(--text-secondary) !important;
        font-weight: 600;
        padding: 12px 18px;
        width: 100%;
        justify-content: center;
        transition: all 0.25s ease;
    }

/* =========================
   BLUE SELECTED AREAS FIX
   ========================= */

/* Tabs (Selected) */
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary), var(--primary-2)) !important;
    color: #ffffff !important;
    box-shadow: 0 8px 20px rgba(111,134,255,0.26);
}

/* FORCE all nested text/icons inside selected tab */
.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
    opacity: 1 !important;
}

/* Primary Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--primary-2)) !important;
    color: #ffffff !important;
    box-shadow: 0 10px 20px rgba(111,134,255,0.24);
}

/* FORCE all nested content inside buttons */
.stButton > button[kind="primary"],
.stButton > button[kind="primary"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
    opacity: 1 !important;
}

/* Fix icons specifically */
.stButton > button[kind="primary"] svg,
.stTabs [aria-selected="true"] svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
}

/* Fix segmented controls (Streamlit tabs/pills) */
[data-baseweb="tab"][aria-selected="true"],
[data-baseweb="tab"][aria-selected="true"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
}

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-2)) !important;
        color: #ffffff !important;
        box-shadow: 0 10px 20px rgba(111,134,255,0.24);
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 26px rgba(111,134,255,0.28);
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.72) !important;
        color: var(--text-primary) !important;
        border: 1px solid rgba(123,132,176,0.18) !important;
        box-shadow: 0 6px 16px rgba(98,109,153,0.08);
    }

    .stButton > button:not([kind="primary"]):hover {
        transform: translateY(-1px);
        background: rgba(255,255,255,0.92) !important;
        box-shadow: 0 12px 24px rgba(98,109,153,0.10);
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stFileUploader > div {
        background: rgba(255,255,255,0.78) !important;
        border: 1px solid rgba(123,132,176,0.18) !important;
        border-radius: 14px !important;
        color: var(--text-primary) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(111,134,255,0.45) !important;
        box-shadow: 0 0 0 4px rgba(111,134,255,0.10) !important;
    }

    .hero-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: 34px;
        margin: 22px 0;
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(14px);
    }

    .response-header {
        background: rgba(255,255,255,0.58);
        border: 1px solid rgba(123,132,176,0.14);
        border-radius: 18px;
        padding: 18px 22px;
        margin: 18px 0 14px 0;
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(10px);
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
    }

    [data-testid="stChatMessage"] > div {
        border-radius: 22px !important;
    }

    .question-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 28px 30px;
        box-shadow: var(--shadow-card);
        backdrop-filter: blur(14px);
        margin-bottom: 8px;
    }

    .question-greeting {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 10px;
        line-height: 1.7;
    }

    .question-label {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 14px;
    }

    .question-text {
        font-size: 1.12rem;
        line-height: 1.8;
        color: var(--text-primary);
        font-weight: 500;
    }

    .feedback-card {
        background: var(--panel-strong);
        border: 1px solid rgba(123,132,176,0.16);
        border-radius: 22px;
        padding: 26px 28px;
        box-shadow: var(--shadow-card);
    }

    .feedback-score {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.1rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 14px;
    }

    .feedback-body {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.8;
    }

    .tip-box {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid rgba(123,132,176,0.12);
        color: var(--text-secondary);
        line-height: 1.8;
    }

    .next-question-divider {
        margin-top: 24px;
        margin-bottom: 16px;
        border: none;
        height: 1px;
        background: linear-gradient(
            to right,
            transparent,
            rgba(123,132,176,0.30),
            transparent
        );
    }

    .next-question-card {
        margin-top: 10px;
        margin-bottom: 16px;
        padding: 24px 28px;
        background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(249,250,255,0.88));
        border: 1px solid rgba(111,134,255,0.24);
        border-radius: 22px;
        box-shadow: 0 14px 34px rgba(98,109,153,0.12);
        backdrop-filter: blur(14px);
    }

    .next-question-label {
        font-size: 0.9rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--primary-3);
        margin-bottom: 10px;
    }

    .next-question-title {
        display: none;
    }

    .next-question-text {
        font-size: 1.1rem;
        color: var(--text-primary);
        line-height: 1.8;
        font-weight: 500;
        margin: 0;
    }

    .processing-overlay {
        position: fixed;
        inset: 0;
        background: rgba(238, 241, 249, 0.58);
        backdrop-filter: blur(7px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999999;
    }

    .processing-modal {
        width: min(660px, 92vw);
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(123,132,176,0.18);
        border-radius: 28px;
        box-shadow: 0 22px 60px rgba(98,109,153,0.18);
        padding: 34px 30px;
        text-align: center;
        backdrop-filter: blur(16px);
    }

    .processing-icon {
        width: 74px;
        height: 74px;
        margin: 0 auto 18px auto;
        border-radius: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        background: linear-gradient(135deg, var(--primary), var(--primary-2));
        color: white;
        box-shadow: 0 14px 30px rgba(111,134,255,0.22);
        animation: processingPulse 1.8s ease-in-out infinite;
    }

    .processing-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 10px;
        line-height: 1.35;
    }

    .processing-subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.7;
        margin-bottom: 18px;
    }

    .processing-status {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        background: rgba(111,134,255,0.08);
        color: var(--text-primary);
        border: 1px solid rgba(111,134,255,0.14);
        border-radius: 999px;
        padding: 10px 18px;
        font-size: 0.98rem;
        font-weight: 700;
    }

    .processing-dots::after {
        content: "";
        display: inline-block;
        width: 24px;
        text-align: left;
        animation: processingDots 1.4s infinite steps(1, end);
    }

    audio {
        border-radius: 14px;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.68);
        border: 1px solid rgba(123,132,176,0.14);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 8px 22px rgba(98,109,153,0.08);
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(123,132,176,0.22), transparent);
    }

    @keyframes processingDots {
        0%   { content: "."; }
        33%  { content: ".."; }
        66%  { content: "..."; }
        100% { content: "."; }
    }

    @keyframes processingPulse {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 14px 30px rgba(111,134,255,0.22);
        }
        50% {
            transform: scale(1.05);
            box-shadow: 0 18px 36px rgba(111,134,255,0.28);
        }
    }
    </style>
    """, unsafe_allow_html=True)


def _get_cookie_token():
    params = st.query_params
    return params.get("session", "")


def _restore_session():
    token = _get_cookie_token()
    if token:
        session_data = get_session(token)
        if session_data:
            st.session_state.logged_in = True
            st.session_state.user_id = session_data["user_id"]
            st.session_state.username = session_data["username"]
            st.session_state.session_token = token
            return True
    return False


def init_session_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": "",
        "page": "interview",
        "cv_text": "",
        "jd_text": "",
        "job_role": "",
        "messages": [],
        "current_question_index": 0,
        "questions": [],
        "answers": [],
        "scores": [],
        "tips": [],
        "justifications": [],
        "interview_started": False,
        "interview_completed": False,
        "seniority": "Mid",
        "awaiting_answer": False,
        "processing": False,
        "processing_mode": "",
        "pending_start": False,
        "pending_text_answer": "",
        "pending_audio_bytes": None,
        "report_generated": False,
        "report_text": "",
        "auto_speak_question": "",
        "has_recording": False,
        "recorded_audio": None,
        "quick_start_role": "",
        "setup_mode": "quick",
        "preferred_input": "audio",
        "session_token": "",
        "session_restored": False,
        "user_tz": None,
        "recorder_version": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.logged_in and not st.session_state.session_restored:
        st.session_state.session_restored = True
        _restore_session()


def reset_interview():
    st.session_state.messages = []
    st.session_state.current_question_index = 0
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.scores = []
    st.session_state.tips = []
    st.session_state.justifications = []
    st.session_state.interview_started = False
    st.session_state.interview_completed = False
    st.session_state.awaiting_answer = False
    st.session_state.processing = False
    st.session_state.processing_mode = ""
    st.session_state.pending_start = False
    st.session_state.pending_text_answer = ""
    st.session_state.pending_audio_bytes = None
    st.session_state.report_generated = False
    st.session_state.report_text = ""
    st.session_state.auto_speak_question = ""
    st.session_state.has_recording = False
    st.session_state.recorded_audio = None
    st.session_state.recorder_version = 0

    keys_to_delete = [k for k in st.session_state.keys() if str(k).startswith("tts_cache_") or str(k).startswith("play_question_")]
    for k in keys_to_delete:
        del st.session_state[k]


def render_auth_page():
    col_spacer1, col_main, col_spacer2 = st.columns([1, 2, 1])

    with col_main:
        st.markdown(
            '<h1 style="margin-bottom: 0;"><span style="font-size: 1.1em;">🎯</span> AI Mock Interview</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color: var(--text-secondary); font-size: 1.2rem; margin-bottom: 24px;">Master your next job interview with AI-powered coaching</p>',
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["🔑 Login", "✨ Create Account"])

        with tab_login:
            login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            if st.button("Login", type="primary", use_container_width=True, key="login_btn"):
                if login_username and login_password:
                    result = verify_user(login_username, login_password)
                    if result["success"]:
                        token = create_session(result["user_id"])
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.session_token = token
                        st.query_params["session"] = token
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.warning("Please enter both username and password")

        with tab_register:
            reg_username = st.text_input("Choose a Username", key="reg_username", placeholder="At least 3 characters")
            reg_password = st.text_input("Choose a Password", type="password", key="reg_password", placeholder="At least 6 characters")
            reg_password2 = st.text_input("Confirm Password", type="password", key="reg_password2", placeholder="Re-enter your password")

            if st.button("Create Account", type="primary", use_container_width=True, key="register_btn"):
                if not reg_username or not reg_password:
                    st.warning("Please fill in all fields")
                elif reg_password != reg_password2:
                    st.error("Passwords do not match")
                else:
                    result = create_user(reg_username, reg_password)
                    if result["success"]:
                        token = create_session(result["user_id"])
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.session_token = token
                        st.query_params["session"] = token
                        st.rerun()
                    else:
                        st.error(result["error"])


def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")

        is_admin = is_admin_user(st.session_state.username)

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("🎯 Interview", use_container_width=True):
                st.session_state.page = "interview"
                st.rerun()
        with col_nav2:
            if st.button("📜 History", use_container_width=True):
                st.session_state.page = "history"
                st.rerun()

        if is_admin:
            if st.button("🛠️ Admin Dashboard", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            token = st.session_state.get("session_token", "")
            if token:
                delete_session(token)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()

        st.divider()

        if st.session_state.page == "interview":
            render_interview_sidebar()


def render_interview_sidebar():
    st.header("📄 Interview Setup")

    quick_tab, full_tab = st.tabs(["⚡ Quick Start", "📄 Full Setup"])

    with quick_tab:
        st.markdown("*Enter a role to start instantly — no CV needed*")

        quick_role = st.text_input(
            "Job Role",
            value=st.session_state.quick_start_role,
            placeholder="e.g. Frontend Developer, Data Analyst...",
        )
        st.session_state.quick_start_role = quick_role

        seniority_q = st.selectbox(
            "Seniority Level",
            SENIORITY_LEVELS,
            index=SENIORITY_LEVELS.index(st.session_state.seniority),
            key="seniority_quick",
        )
        st.session_state.seniority = seniority_q

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            start_disabled = st.session_state.interview_started or st.session_state.processing
            if st.button("▶️ Start", disabled=start_disabled, use_container_width=True, key="quick_start_btn"):
                role_value = quick_role.strip()
                if role_value:
                    st.session_state.setup_mode = "quick"
                    st.session_state.cv_text = f"Role: {role_value}"
                    st.session_state.jd_text = f"{role_value} position"
                    st.session_state.processing = True
                    st.session_state.processing_mode = "setup"
                    st.session_state.pending_start = True
                    st.rerun()
                else:
                    st.warning("Please enter a job role first, then click Start again.")
        with col2:
            if st.button("🔄 Restart", use_container_width=True, key="quick_restart_btn"):
                reset_interview()
                st.rerun()

    with full_tab:
        st.markdown("*Upload your CV for tailored questions*")

        full_role = st.text_input(
            "Job Role",
            value=st.session_state.job_role,
            placeholder="e.g. Accountant, Admin Officer, Project Engineer...",
            key="full_setup_job_role",
        )
        st.session_state.job_role = full_role

        uploaded_file = st.file_uploader(
            "Upload CV/Resume (PDF, Word, TXT)",
            type=["pdf", "docx", "txt"],
            key="cv_upload",
        )

        if uploaded_file:
            cv_text, error = parse_document(uploaded_file)
            if error:
                st.error(f"⚠️ {error}")
            else:
                st.session_state.cv_text = cv_text
                st.success(f"✅ CV loaded ({len(cv_text.split())} words)")

        st.divider()

        jd_text = st.text_area(
            "Job Description (Optional)",
            value=st.session_state.jd_text if st.session_state.setup_mode == "full" else "",
            height=120,
            placeholder="Paste job requirements here...",
            key="full_setup_jd",
        )
        st.session_state.jd_text = jd_text

        st.divider()

        seniority_f = st.selectbox(
            "Seniority Level",
            SENIORITY_LEVELS,
            index=SENIORITY_LEVELS.index(st.session_state.seniority),
            key="seniority_full",
        )
        st.session_state.seniority = seniority_f

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            start_disabled = (
                not st.session_state.cv_text
                or not st.session_state.job_role.strip()
                or st.session_state.interview_started
                or st.session_state.processing
            )

            if st.button("▶️ Start", disabled=start_disabled, use_container_width=True, key="full_start_btn"):
                st.session_state.setup_mode = "full"

                cv_for_interview = st.session_state.cv_text
                if st.session_state.job_role.strip():
                    cv_for_interview = f"Target Role: {st.session_state.job_role.strip()}\n\n{cv_for_interview}"

                st.session_state.cv_text = cv_for_interview
                st.session_state.processing = True
                st.session_state.processing_mode = "setup"
                st.session_state.pending_start = True
                st.rerun()

        with col2:
            if st.button("🔄 Restart", use_container_width=True, key="full_restart_btn"):
                reset_interview()
                st.rerun()

        if not st.session_state.job_role.strip():
            st.info("👆 Enter the target job role.")
        elif not st.session_state.cv_text:
            st.info("👆 Upload your CV to begin")


def _start_interview_now():
    reset_interview()
    st.session_state.interview_started = True

    role_text = st.session_state.job_role.strip() or (
        st.session_state.cv_text.replace("Role: ", "").strip() if st.session_state.cv_text else "this role"
    )

    try:
        result = get_first_question(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority,
            demo_mode=False,
        )

        greeting = result.get("greeting", "Hello, thank you for interviewing today.")
        first_question = result.get("question", "Tell me about yourself and your relevant experience.")

        if not first_question or not str(first_question).strip():
            first_question = f"Why are you a good fit for the {role_text} role?"

    except Exception as e:
        st.warning(f"AI question generation failed. Using fallback question instead. Error: {str(e)}")
        greeting = "Hello, thank you for interviewing today."
        first_question = f"Why are you a good fit for the {role_text} role?"

    safe_greeting = html.escape(greeting)
    safe_question = html.escape(first_question)

    full_message = f"""
<div class="question-card">
    <div class="question-greeting">{safe_greeting}</div>
    <div class="question-label">🎯 Question 1/{TOTAL_QUESTIONS}</div>
    <div class="question-text">{safe_question}</div>
</div>
"""

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_message,
    })
    st.session_state.questions.append(first_question)
    st.session_state.current_question_index = 1
    st.session_state.awaiting_answer = True
    st.session_state.auto_speak_question = first_question


def _process_answer_now(transcription: str):
    st.session_state.messages.append({
        "role": "user",
        "content": transcription,
    })
    st.session_state.answers.append(transcription)

    conversation_history = []
    for msg in st.session_state.messages[:-1]:
        conversation_history.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    try:
        result = evaluate_answer_and_get_next(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority,
            conversation_history,
            transcription,
            st.session_state.current_question_index,
            demo_mode=False,
        )

        score = result.get("score", 5)
        justification = result.get("justification", "No justification returned.")
        pro_tip = result.get("pro_tip", "No pro tip returned.")
        next_question = result.get("next_question")

        st.session_state.scores.append(score)
        st.session_state.tips.append(pro_tip)
        st.session_state.justifications.append(justification)

        feedback_message = f"""
<div class="feedback-card">
    <div class="feedback-score">⭐ Score: {score}/10</div>
    <div class="feedback-body">{html.escape(justification)}</div>
    <div class="tip-box">💡 <strong>Pro Tip:</strong> {html.escape(pro_tip)}</div>
</div>
"""

        is_last_question = st.session_state.current_question_index >= TOTAL_QUESTIONS

        if not is_last_question:
            if not next_question:
                raise ValueError("OpenAI did not return the next question.")

            st.session_state.current_question_index += 1
            st.session_state.has_recording = False
            st.session_state.recorded_audio = None
            st.session_state.recorder_version += 1
            st.session_state.awaiting_answer = True
            st.session_state.auto_speak_question = next_question
            st.session_state.questions.append(next_question)

            safe_next_question = html.escape(next_question)

            feedback_message += f"""
<div class="next-question-divider"></div>
<div class="next-question-card">
    <div class="next-question-label">Next Question</div>
    <p class="next-question-text">{safe_next_question}</p>
</div>
"""
        else:
            st.session_state.interview_completed = True
            st.session_state.awaiting_answer = False
            feedback_message += """
<hr />
<p style="margin-top:16px; color:#2c3353; font-weight:700;">🎉 Interview Complete!</p>
<p style="margin-top:6px; color:#677095;">Click 'Generate Performance Report' below to get your detailed report.</p>
"""

        st.session_state.messages.append({
            "role": "assistant",
            "content": feedback_message,
        })

    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ OpenAI evaluation failed.<br><br>Error: {html.escape(str(e))}",
        })
        st.session_state.awaiting_answer = True


def run_pending_actions():
    if st.session_state.pending_start:
        st.session_state.pending_start = False
        try:
            _start_interview_now()
        finally:
            st.session_state.processing = False
            st.session_state.processing_mode = ""
        st.rerun()

    if st.session_state.pending_audio_bytes is not None:
        audio_bytes = st.session_state.pending_audio_bytes
        st.session_state.pending_audio_bytes = None

        try:
            transcribed_text, error = speech_to_text(audio_bytes)

            if error:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ Could not transcribe audio.<br><br>Error: {html.escape(error)}",
                })
                st.session_state.awaiting_answer = True
            elif transcribed_text:
                _process_answer_now(transcribed_text)
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "⚠️ No speech detected. Please try recording again.",
                })
                st.session_state.awaiting_answer = True

        finally:
            st.session_state.processing = False
            st.session_state.processing_mode = ""
        st.rerun()

    if st.session_state.pending_text_answer:
        pending_text = st.session_state.pending_text_answer
        st.session_state.pending_text_answer = ""

        try:
            _process_answer_now(pending_text)
        finally:
            st.session_state.processing = False
            st.session_state.processing_mode = ""
        st.rerun()


def render_processing_overlay():
    if not st.session_state.processing:
        return

    if st.session_state.processing_mode == "setup":
        icon = "🎯"
        title = "Setting up your interview, please wait"
        subtitle = "Preparing your greeting, generating your first question, and getting everything ready."
        status_text = "Building your interview"
    else:
        icon = "🤖"
        title = "Transcribing and evaluating your response, please wait"
        subtitle = "Reviewing your answer, scoring it, generating your pro tip, and preparing the next question."
        status_text = "Analyzing your response"

    st.markdown(f"""
    <div class="processing-overlay">
        <div class="processing-modal">
            <div class="processing-icon">{icon}</div>
            <div class="processing-title">{title}</div>
            <div class="processing-subtitle">{subtitle}</div>
            <div class="processing-status">
                {status_text}<span class="processing-dots"></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat():
    question_idx = 0

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

            if message["role"] == "assistant" and question_idx < len(st.session_state.questions):
                q_text = st.session_state.questions[question_idx]
                audio_key = f"tts_cache_{question_idx}"
                play_key = f"play_question_{question_idx}"

                if st.button("🔊 Listen to Question", key=f"listen_{question_idx}"):
                    if audio_key not in st.session_state:
                        audio_bytes, error = text_to_speech(q_text)
                        if audio_bytes:
                            st.session_state[audio_key] = audio_bytes
                            st.session_state[play_key] = True
                            st.rerun()
                        else:
                            st.error(f"Could not generate audio: {error}")
                    else:
                        st.session_state[play_key] = True
                        st.rerun()

                if audio_key in st.session_state:
                    autoplay_now = st.session_state.get(play_key, False)
                    st.audio(
                        st.session_state[audio_key],
                        format="audio/wav",
                        autoplay=autoplay_now,
                    )
                    if autoplay_now:
                        st.session_state[play_key] = False

                question_idx += 1

    if st.session_state.auto_speak_question:
        question_text = st.session_state.auto_speak_question
        st.session_state.auto_speak_question = ""

        audio_bytes, error = text_to_speech(question_text)
        if audio_bytes:
            cache_idx = len(st.session_state.questions) - 1
            cache_key = f"tts_cache_{cache_idx}"
            play_key = f"play_question_{cache_idx}"

            st.session_state[cache_key] = audio_bytes
            st.session_state[play_key] = True
            st.audio(audio_bytes, format="audio/wav", autoplay=True)


def finish_interview_button(key: str):
    if st.button("🏁 Finish Interview", use_container_width=True, type="primary", key=key):
        st.session_state.interview_completed = True
        st.session_state.awaiting_answer = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"🎉 <strong>Interview Finished!</strong> You answered {len(st.session_state.answers)} out of {TOTAL_QUESTIONS} questions. Click 'Generate Performance Report' below to get your detailed report.",
        })
        st.rerun()


def render_response_input():
    if st.session_state.processing or not st.session_state.awaiting_answer:
        return

    st.markdown("---")
    st.markdown(f"""
    <div class="response-header">
        <span style="font-size: 1.3rem; font-weight: 600; color: var(--text-primary);">
            ✍️ Your Response — Question {st.session_state.current_question_index} of {TOTAL_QUESTIONS}
        </span>
    </div>
    """, unsafe_allow_html=True)

    answer_key = f"answer_{st.session_state.current_question_index}_{len(st.session_state.answers)}"

    if st.session_state.preferred_input == "text":
        tab_text, tab_audio = st.tabs(["⌨️ Type Answer", "🎙️ Record Answer"])
    else:
        tab_audio, tab_text = st.tabs(["🎙️ Record Answer", "⌨️ Type Answer"])

    with tab_audio:
        st.session_state.preferred_input = "audio"

        st.markdown("### Record your answer")
        st.caption("Record your answer, then preview and submit.")

        if not st.session_state.has_recording:
            audio_file = st.audio_input(
                "Tap to record",
                key=f"audio_input_q{st.session_state.current_question_index}_v{st.session_state.get('recorder_version', 0)}",
            )

            if audio_file is not None:
                st.session_state.recorded_audio = audio_file.read()
                st.session_state.has_recording = True
                st.rerun()

        if st.session_state.has_recording and st.session_state.recorded_audio:
            stored_audio = st.session_state.recorded_audio

            st.markdown("""
            <div style="background: rgba(59,178,115,0.08); border: 1px solid rgba(59,178,115,0.18);
                border-radius: 14px; padding: 12px 16px; margin: 12px 0;">
                <span style="color: #2f9d63; font-weight: 700;">✅ Recording captured!</span>
                <span style="color: var(--text-secondary);"> Preview below, then submit or re-record.</span>
            </div>
            """, unsafe_allow_html=True)

            st.audio(stored_audio, format="audio/wav")

            col_submit, col_rerecord = st.columns(2)

            with col_submit:
                if st.button(
                    "🎤 Submit Audio Answer",
                    type="primary",
                    use_container_width=True,
                    key=f"audio_submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}",
                ):
                    st.session_state.has_recording = False
                    st.session_state.recorded_audio = None
                    st.session_state.recorder_version += 1
                    st.session_state.processing = True
                    st.session_state.processing_mode = "answer"
                    st.session_state.pending_audio_bytes = stored_audio
                    st.rerun()

            with col_rerecord:
                if st.button(
                    "🔄 Re-record",
                    use_container_width=True,
                    key=f"rerecord_{st.session_state.current_question_index}_{len(st.session_state.answers)}",
                ):
                    st.session_state.has_recording = False
                    st.session_state.recorded_audio = None
                    st.session_state.recorder_version += 1
                    st.rerun()
        else:
            st.info("Recorder is ready.")

        if len(st.session_state.answers) >= 1:
            finish_interview_button(f"finish_audio_{st.session_state.current_question_index}")

    with tab_text:
        text_answer = st.text_area(
            "Type your answer here",
            key=answer_key,
            height=200,
            placeholder="Take your time and provide a detailed response...",
        )

        submit_key = f"submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}"

        if st.button("📝 Submit Text Answer", type="primary", key=submit_key, use_container_width=True):
            if text_answer.strip():
                st.session_state.preferred_input = "text"
                st.session_state.processing = True
                st.session_state.processing_mode = "answer"
                st.session_state.pending_text_answer = text_answer.strip()
                st.rerun()
            else:
                st.warning("Please enter your answer before submitting.")

        if len(st.session_state.answers) >= 1:
            finish_interview_button(f"finish_text_{st.session_state.current_question_index}")


def render_final_report():
    if not st.session_state.interview_completed:
        return

    st.markdown("---")

    if st.session_state.report_generated:
        avg_score = sum(st.session_state.scores) / len(st.session_state.scores)

        st.markdown("""
        <div style="background: rgba(255,255,255,0.72);
            border: 1px solid rgba(123,132,176,0.16); border-radius: 20px; padding: 24px; margin-bottom: 20px;
            box-shadow: 0 10px 26px rgba(98,109,153,0.08);">
            <h2 style="color: #2c3353; margin: 0 0 8px 0;">📋 Your Interview Performance Report</h2>
            <p style="color: #677095; margin: 0;">Personalized analysis based on your interview</p>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(3)
        with cols[0]:
            st.metric("Overall Performance", f"{avg_score:.1f}/10")
        with cols[1]:
            st.metric("Questions Answered", len(st.session_state.answers))
        with cols[2]:
            performance = "Excellent" if avg_score >= 8 else "Good" if avg_score >= 6 else "Needs Work"
            st.metric("Performance Level", performance)

        st.markdown("---")
        st.markdown(st.session_state.report_text)
        st.markdown("---")
        st.success("✅ This interview and report have been saved to your history.")
        return

    if st.button("📊 Generate Performance Report", type="primary", use_container_width=True):
        try:
            report = generate_final_report(
                st.session_state.cv_text,
                st.session_state.jd_text,
                st.session_state.seniority,
                st.session_state.questions,
                st.session_state.answers,
                st.session_state.scores,
                st.session_state.tips,
                demo_mode=False,
            )

            st.session_state.report_generated = True
            st.session_state.report_text = report

            avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
            save_interview(
                user_id=st.session_state.user_id,
                seniority=st.session_state.seniority,
                demo_mode=False,
                cv_text=st.session_state.cv_text,
                jd_text=st.session_state.jd_text,
                questions=st.session_state.questions,
                answers=st.session_state.answers,
                scores=st.session_state.scores,
                tips=st.session_state.tips,
                justifications=st.session_state.justifications,
                report=report,
                avg_score=avg_score,
            )

            st.rerun()

        except Exception as e:
            st.error(f"Failed to generate report: {str(e)}")


def get_user_timezone():
    if st.session_state.user_tz is None:
        tz_param = st.query_params.get("tz")
        if tz_param:
            st.session_state.user_tz = tz_param
        else:
            st.session_state.user_tz = "UTC"

    return st.session_state.user_tz


def format_interview_time(dt, tz_name):
    if not dt:
        return "Unknown"

    try:
        if isinstance(dt, str):
            dt = dt.strip()
            if dt.endswith("Z"):
                dt = dt.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        user_tz = ZoneInfo(tz_name)
        local_dt = dt.astimezone(user_tz)
        return local_dt.strftime("%B %d, %Y at %I:%M %p")

    except Exception:
        try:
            return str(dt)
        except Exception:
            return "Unknown"


def render_history_page():
    st.title("📜 Interview History")
    st.markdown(
        f'<p style="color: var(--text-secondary);">Past interviews for <strong style="color: var(--primary-3);">{st.session_state.username}</strong></p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    user_tz = get_user_timezone()
    interviews = get_user_interviews(st.session_state.user_id)

    if not interviews:
        st.info("No interviews yet. Go to the Interview page to start your first one!")
        return

    for i, interview in enumerate(interviews):
        created = format_interview_time(interview["created_at"], user_tz)
        avg = interview["avg_score"] or 0
        mode = "Demo" if interview["demo_mode"] else "AI"
        label = f"**{created}** — Score: {avg:.1f}/10 — {interview['seniority']} level — {mode} Mode"

        with st.expander(label, expanded=(i == 0)):
            cols = st.columns(3)
            with cols[0]:
                st.metric("Average Score", f"{avg:.1f}/10")
            with cols[1]:
                st.metric("Seniority", interview["seniority"])
            with cols[2]:
                performance = "Excellent" if avg >= 8 else "Good" if avg >= 6 else "Needs Work"
                st.metric("Performance", performance)

            st.markdown("---")

            raw_q = interview["questions"]
            raw_a = interview["answers"]
            raw_s = interview["scores"]
            raw_t = interview["tips"]
            questions = raw_q if isinstance(raw_q, list) else (json.loads(raw_q) if isinstance(raw_q, str) else [])
            answers = raw_a if isinstance(raw_a, list) else (json.loads(raw_a) if isinstance(raw_a, str) else [])
            scores = raw_s if isinstance(raw_s, list) else (json.loads(raw_s) if isinstance(raw_s, str) else [])
            tips = raw_t if isinstance(raw_t, list) else (json.loads(raw_t) if isinstance(raw_t, str) else [])

            for j in range(len(questions)):
                st.markdown(f"**Question {j+1}:** {questions[j]}")
                if j < len(answers):
                    st.markdown(f"**Your Answer:** {answers[j]}")
                if j < len(scores):
                    st.markdown(f"**Score:** {scores[j]}/10")
                if j < len(tips):
                    st.markdown(f"💡 **Pro Tip:** {tips[j]}")
                st.markdown("---")

            if interview.get("report"):
                st.markdown("### 📋 Feedback Report")
                st.markdown(interview["report"])


def _safe_to_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None


def render_admin_page():
    st.markdown('<h1 style="margin-bottom: 0;"><span style="font-size: 1.1em;">🛠️</span> Admin Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-secondary); font-size: 1.1rem;">Platform analytics, user insights, and data export</p>', unsafe_allow_html=True)
    st.markdown("---")

    all_interviews = get_all_interviews_admin()
    all_users = get_all_users_admin()

    if not all_interviews:
        st.info("No interview data found yet.")
        return

    for iv in all_interviews:
        for field in ["questions", "answers", "scores", "tips", "justifications"]:
            raw = iv[field]
            if isinstance(raw, str):
                try:
                    iv[field] = json.loads(raw)
                except Exception:
                    iv[field] = []
            elif raw is None:
                iv[field] = []

    total_users = len(all_users)
    total_interviews = len(all_interviews)
    scores_flat = [iv["avg_score"] for iv in all_interviews if iv["avg_score"] is not None]
    platform_avg = round(sum(scores_flat) / len(scores_flat), 2) if scores_flat else 0

    now_utc = datetime.now(timezone.utc)
    week_ago = now_utc - timedelta(days=7)
    interviews_this_week = 0

    for iv in all_interviews:
        dt = _safe_to_datetime(iv.get("created_at"))
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= week_ago:
                interviews_this_week += 1

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Users", total_users)
    with m2:
        st.metric("Total Interviews", total_interviews)
    with m3:
        st.metric("Platform Avg Score", f"{platform_avg}/10")
    with m4:
        st.metric("Interviews This Week", interviews_this_week)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Score Distribution")
        buckets = {"0-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
        for s in scores_flat:
            if s < 4:
                buckets["0-4"] += 1
            elif s < 6:
                buckets["4-6"] += 1
            elif s < 8:
                buckets["6-8"] += 1
            else:
                buckets["8-10"] += 1
        score_df = pd.DataFrame({"Score Range": list(buckets.keys()), "Interviews": list(buckets.values())})
        score_df = score_df.set_index("Score Range")
        st.bar_chart(score_df)

    with col_right:
        st.subheader("Seniority Breakdown")
        seniority_counts = {}
        for iv in all_interviews:
            s = iv["seniority"] or "Unknown"
            seniority_counts[s] = seniority_counts.get(s, 0) + 1
        sen_df = pd.DataFrame({"Seniority": list(seniority_counts.keys()), "Interviews": list(seniority_counts.values())})
        sen_df = sen_df.set_index("Seniority")
        st.bar_chart(sen_df)

    st.markdown("---")
    st.subheader("Interviews Over Time (Daily)")
    dates = []
    for iv in all_interviews:
        dt = _safe_to_datetime(iv.get("created_at"))
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dates.append(dt.date())

    if dates:
        date_counts = {}
        for d in dates:
            date_counts[d] = date_counts.get(d, 0) + 1
        sorted_dates = sorted(date_counts.keys())
        timeline_df = pd.DataFrame({"Date": sorted_dates, "Interviews": [date_counts[d] for d in sorted_dates]})
        timeline_df = timeline_df.set_index("Date")
        st.line_chart(timeline_df)

    st.markdown("---")
    st.subheader("Average Score Over Time (7-Day Rolling)")
    if len(all_interviews) >= 2:
        score_date_rows = []
        for iv in all_interviews:
            dt = _safe_to_datetime(iv.get("created_at"))
            if dt and iv["avg_score"] is not None:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                score_date_rows.append({"Date": dt.date(), "avg_score": iv["avg_score"]})

        if score_date_rows:
            score_time_df = pd.DataFrame(score_date_rows).sort_values("Date")
            score_time_df = score_time_df.groupby("Date")["avg_score"].mean().reset_index()
            score_time_df["7-Day Rolling Avg"] = score_time_df["avg_score"].rolling(7, min_periods=1).mean().round(2)
            score_time_df = score_time_df.set_index("Date")[["7-Day Rolling Avg"]]
            st.line_chart(score_time_df)

    st.markdown("---")
    st.subheader("Top Roles Practiced")
    role_counts = {}
    for iv in all_interviews:
        cv = iv.get("cv_text") or ""
        if cv.startswith("Role: "):
            role = cv.replace("Role: ", "").strip()
        elif cv.startswith("Target Role: "):
            first_line = cv.splitlines()[0]
            role = first_line.replace("Target Role: ", "").strip()
        else:
            role = "Custom CV"
        role_counts[role] = role_counts.get(role, 0) + 1

    sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    if sorted_roles:
        role_df = pd.DataFrame(sorted_roles, columns=["Role", "Interviews"]).set_index("Role")
        st.bar_chart(role_df)

    st.markdown("---")
    st.subheader("User Summary")
    user_rows = []
    for u in all_users:
        joined_dt = _safe_to_datetime(u.get("created_at"))
        user_rows.append({
            "Username": u["username"],
            "Joined": joined_dt.strftime("%Y-%m-%d") if joined_dt else "",
            "Interviews": int(u["interview_count"] or 0),
            "Avg Score": float(u["avg_score"]) if u["avg_score"] is not None else None,
        })
    user_summary_df = pd.DataFrame(user_rows)
    st.dataframe(user_summary_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("All Interviews")

    filter_user = st.text_input("Filter by username", placeholder="Type to filter...")
    filter_seniority = st.selectbox("Filter by seniority", ["All"] + SENIORITY_LEVELS)

    filtered = all_interviews
    if filter_user.strip():
        filtered = [iv for iv in filtered if filter_user.strip().lower() in iv["username"].lower()]
    if filter_seniority != "All":
        filtered = [iv for iv in filtered if iv["seniority"] == filter_seniority]

    st.caption(f"Showing {len(filtered)} of {total_interviews} interviews")

    for i, iv in enumerate(filtered):
        created_dt = _safe_to_datetime(iv.get("created_at"))
        created_str = created_dt.strftime("%Y-%m-%d %H:%M") if created_dt else "Unknown"
        avg = iv["avg_score"] or 0
        label = f"**{iv['username']}** — {created_str} — {iv['seniority']} — Score: {avg:.1f}/10"

        with st.expander(label, expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Score", f"{avg:.1f}/10")
            with c2:
                st.metric("Seniority", iv["seniority"] or "N/A")
            with c3:
                performance = "Excellent" if avg >= 8 else "Good" if avg >= 6 else "Needs Work"
                st.metric("Performance", performance)

            cv = iv.get("cv_text") or ""
            if cv.startswith("Role: "):
                st.markdown(f"**Role (Quick Start):** {cv.replace('Role: ', '').strip()}")
            elif cv.startswith("Target Role: "):
                first_line = cv.splitlines()[0]
                st.markdown(f"**Target Role:** {first_line.replace('Target Role: ', '').strip()}")
                with st.expander("View CV Text"):
                    cv_body = "\n".join(cv.splitlines()[2:]) if len(cv.splitlines()) > 2 else ""
                    st.text(cv_body[:1000] + ("..." if len(cv_body) > 1000 else ""))
            else:
                with st.expander("View CV Text"):
                    st.text(cv[:1000] + ("..." if len(cv) > 1000 else ""))

            jd = iv.get("jd_text") or ""
            if jd and not jd.endswith("position"):
                with st.expander("View Job Description"):
                    st.text(jd[:500] + ("..." if len(jd) > 500 else ""))

            st.markdown("---")
            questions = iv["questions"] or []
            answers = iv["answers"] or []
            scores = iv["scores"] or []
            tips = iv["tips"] or []

            for j in range(len(questions)):
                st.markdown(f"**Q{j+1}:** {questions[j]}")
                if j < len(answers):
                    st.markdown(f"**Answer:** {answers[j]}")
                if j < len(scores):
                    st.markdown(f"**Score:** {scores[j]}/10")
                if j < len(tips):
                    st.markdown(f"💡 **Tip:** {tips[j]}")
                if j < len(questions) - 1:
                    st.markdown("---")

            if iv.get("report"):
                st.markdown("---")
                st.markdown("**Final Report:**")
                st.markdown(iv["report"])

    st.markdown("---")
    st.subheader("Export Data")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        st.markdown("**Summary Export** — One row per interview")
        summary_rows = []
        for iv in all_interviews:
            created_dt = _safe_to_datetime(iv.get("created_at"))
            cv = iv.get("cv_text") or ""

            if cv.startswith("Role: "):
                role = cv.replace("Role: ", "").strip()
            elif cv.startswith("Target Role: "):
                role = cv.splitlines()[0].replace("Target Role: ", "").strip()
            else:
                role = "Custom CV"

            summary_rows.append({
                "interview_id": iv["id"],
                "username": iv["username"],
                "date": created_dt.strftime("%Y-%m-%d %H:%M") if created_dt else "",
                "seniority": iv["seniority"],
                "avg_score": iv["avg_score"],
                "performance": "Excellent" if (iv["avg_score"] or 0) >= 8 else "Good" if (iv["avg_score"] or 0) >= 6 else "Needs Work",
                "role": role,
                "has_report": bool(iv.get("report")),
            })

        summary_df = pd.DataFrame(summary_rows)
        csv_summary = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Summary CSV",
            data=csv_summary,
            file_name="interviews_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_exp2:
        st.markdown("**Full Q&A Export** — One row per question/answer")
        qa_rows = []
        for iv in all_interviews:
            created_dt = _safe_to_datetime(iv.get("created_at"))
            questions = iv["questions"] or []
            answers = iv["answers"] or []
            scores = iv["scores"] or []
            tips = iv["tips"] or []

            for j in range(len(questions)):
                qa_rows.append({
                    "interview_id": iv["id"],
                    "username": iv["username"],
                    "date": created_dt.strftime("%Y-%m-%d %H:%M") if created_dt else "",
                    "seniority": iv["seniority"],
                    "avg_score": iv["avg_score"],
                    "question_num": j + 1,
                    "question": questions[j] if j < len(questions) else "",
                    "answer": answers[j] if j < len(answers) else "",
                    "score": scores[j] if j < len(scores) else "",
                    "tip": tips[j] if j < len(tips) else "",
                })

        qa_df = pd.DataFrame(qa_rows)
        csv_qa = qa_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Full Q&A CSV",
            data=csv_qa,
            file_name="interviews_full_qa.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_interview_page():
    st.markdown('<h1 style="margin-bottom: 0;"><span style="font-size: 1.1em;">🎯</span> AI Mock Interview</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-secondary); font-size: 1.1rem;">Practice your interview skills with AI-powered coaching</p>', unsafe_allow_html=True)

    if st.session_state.processing:
        render_processing_overlay()
        run_pending_actions()
        return

    if not st.session_state.interview_started:
        st.markdown("---")

        st.markdown("""
        <div class="hero-card">
            <h3 style="color: var(--text-primary) !important; margin-top: 0;">Welcome! 👋</h3>
            <p style="color: var(--text-secondary);">Get ready to ace your next interview with personalized AI coaching.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **How it works:**
            1. ⚡ **Quick Start**: Enter a role + seniority in the sidebar
            2. *Or* 📄 **Full Setup**: Enter target role + upload CV + job description
            3. ▶️ Click "Start" to begin
            4. ✍️ Answer the interview question
            5. 📊 Get instant feedback and a final report
            """)
        with col2:
            st.markdown("""
            **Features:**
            - ⚡ **Quick Start**: No CV needed — just pick a role
            - 🎯 **Targeted Full Setup**: Uses Job Role + CV + JD
            - 📈 **Instant Scoring**: 0-10 on your answer
            - 💡 **Pro Tips**: Actionable advice
            - 📋 **Final Report**: Feedback with practice plan
            - 📜 **History**: All interviews saved to your account
            """)
    else:
        render_chat()
        render_response_input()
        render_final_report()


def main():
    st.set_page_config(
        page_title="AI Mock Interview",
        page_icon="🎯",
        layout="wide",
    )

    inject_custom_css()
    init_db()
    init_session_state()

    if not st.session_state.logged_in:
        render_auth_page()
        return

    render_sidebar()


    if st.session_state.page == "history":
        render_history_page()
    elif st.session_state.page == "admin" and is_admin_user(st.session_state.username):
        render_admin_page()
    else:
        render_interview_page()


if __name__ == "__main__":
    main()