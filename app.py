"""
AI Mock Interview Platform
Main Streamlit application with interview functionality.
"""

import json
import base64
from datetime import timezone
from zoneinfo import ZoneInfo
import streamlit as st

from audio_recorder_streamlit import audio_recorder

import pandas as pd
from config import SENIORITY_LEVELS, TOTAL_QUESTIONS, ADMIN_USERNAME
from utils.pdf_parser import parse_document
from utils.voice import speech_to_text, text_to_speech
from utils.interview_engine import (
    get_first_question,
    evaluate_answer_and_get_next,
    generate_final_report
)
from utils.db import init_db, create_user, verify_user, save_interview, get_user_interviews, get_all_interviews_admin, get_all_users_admin


def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --text-primary: #2d2b3d;
        --text-secondary: #6b6b8d;
        --text-accent: #3b5fc0;
        --text-loading: #4a6fd0;
        --text-body: #4a4868;
        --text-hero-title: #2d2b3d;
        --text-hero-body: #6b6b8d;
        --text-mic-idle: #4a6fd0;
    }

    .stApp {
        background: linear-gradient(145deg, #eef1fa 0%, #e8ecf8 25%, #eae4f4 50%, #e8ecf8 75%, #eef1fa 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0eef8 0%, #ebe8f5 30%, #e6e3f2 60%, #eae8f4 100%);
        border-right: 1px solid rgba(120,100,200,0.1);
        box-shadow: 2px 0 20px rgba(100,80,180,0.05);
    }

    [data-testid="stSidebar"] * {
        color: #2d2b3d !important;
    }

    h1 {
        background: linear-gradient(135deg, #3b5fc0, #5b4fc8, #4a6fd0);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
    }

    h1 span {
        -webkit-text-fill-color: initial !important;
    }

    h2, h3 {
        color: #2d2b3d !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(120,100,200,0.06);
        border-radius: 14px;
        padding: 4px;
        border: 1px solid rgba(120,100,200,0.1);
    }

    .stTabs [data-baseweb="tab-list"] button {
        flex: 1;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #6b6b8d !important;
        font-weight: 500;
        padding: 10px 24px;
        width: 100%;
        justify-content: center;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b5fc0, #5b4fc8) !important;
        color: #ffffff !important;
        box-shadow: 0 3px 12px rgba(59,95,192,0.35);
    }

    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        border: none;
        letter-spacing: 0.02em;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b5fc0 0%, #4a6fd0 50%, #5b7fdf 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 18px rgba(59,95,192,0.35);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 28px rgba(59,95,192,0.45);
        transform: translateY(-2px);
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.8) !important;
        color: #4a4868 !important;
        border: 1px solid rgba(120,100,200,0.18) !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(255,255,255,1) !important;
        border-color: rgba(120,100,200,0.3) !important;
        box-shadow: 0 2px 10px rgba(100,80,180,0.08);
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.85) !important;
        border: 1px solid rgba(120,100,200,0.15) !important;
        border-radius: 12px !important;
        color: #2d2b3d !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #9a98b2 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #5b4fc8 !important;
        box-shadow: 0 0 0 3px rgba(91,79,200,0.1) !important;
    }

    .stSelectbox > div > div {
        background: rgba(255,255,255,0.85) !important;
        border: 1px solid rgba(120,100,200,0.15) !important;
        border-radius: 12px !important;
        color: #2d2b3d !important;
    }

    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stFileUploader label, .stRadio label, .stCheckbox label {
        color: #5a5878 !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.75);
        border: 1px solid rgba(120,100,200,0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(100,80,180,0.06);
        backdrop-filter: blur(10px);
    }

    [data-testid="stMetric"] label {
        color: #7a789a !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.08em;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #3b5fc0 !important;
        font-weight: 700 !important;
    }

    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(120,100,200,0.08);
        border-radius: 14px;
        backdrop-filter: blur(10px);
    }

    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.75) !important;
        border: 1px solid rgba(120,100,200,0.08) !important;
        border-radius: 14px !important;
        padding: 18px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 2px 8px rgba(100,80,180,0.04) !important;
        backdrop-filter: blur(10px) !important;
    }

    .stMarkdown p, .stMarkdown li {
        color: #4a4868;
    }

    .stAlert > div {
        border-radius: 12px !important;
    }

    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.7);
        border: 1px dashed rgba(120,100,200,0.25);
        border-radius: 14px;
        padding: 10px;
    }

    .hero-card {
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(120,100,200,0.1);
        border-radius: 20px;
        padding: 36px;
        margin: 20px 0;
        box-shadow: 0 4px 20px rgba(100,80,180,0.06);
        backdrop-filter: blur(10px);
    }

    .stat-pill {
        display: inline-block;
        background: linear-gradient(135deg, #3b5fc0, #5b4fc8);
        color: #ffffff;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 2px 4px;
    }

    .response-header {
        background: linear-gradient(135deg, rgba(59,95,192,0.08), rgba(91,79,200,0.08));
        border: 1px solid rgba(120,100,200,0.12);
        border-radius: 14px;
        padding: 16px 20px;
        margin: 16px 0 12px 0;
    }

    hr {
        border-color: rgba(120,100,200,0.08) !important;
    }

    .stDivider {
        border-color: rgba(120,100,200,0.08) !important;
    }

    [data-testid="stSidebar"] .stDivider hr,
    [data-testid="stSidebar"] hr {
        border-color: rgba(120,100,200,0.12) !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    defaults = {
        'logged_in': False,
        'user_id': None,
        'username': '',
        'page': 'interview',
        'cv_text': '',
        'jd_text': '',
        'messages': [],
        'current_question_index': 0,
        'questions': [],
        'answers': [],
        'scores': [],
        'tips': [],
        'justifications': [],
        'interview_started': False,
        'interview_completed': False,
        'seniority': 'Mid',
        'awaiting_answer': False,
        'processing': False,
        'report_generated': False,
        'report_text': '',
        'auto_speak_question': '',
        'recorder_version': 0,
        'has_recording': False,
        'quick_start_role': '',
        'setup_mode': 'quick',
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
    st.session_state.report_generated = False
    st.session_state.report_text = ''
    st.session_state.auto_speak_question = ''


def render_auth_page():
    col_spacer1, col_main, col_spacer2 = st.columns([1, 2, 1])

    with col_main:
        st.markdown('<h1 style="margin-bottom: 0;"><span style="font-size: 1.1em;">🎯</span> AI Mock Interview</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: var(--text-secondary); font-size: 1.2rem; margin-bottom: 24px;">Master your next job interview with AI-powered coaching</p>', unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Login", "✨ Create Account"])

        with tab_login:
            st.markdown("")
            login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            if st.button("Login", type="primary", use_container_width=True, key="login_btn"):
                if login_username and login_password:
                    result = verify_user(login_username, login_password)
                    if result["success"]:
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.warning("Please enter both username and password")

        with tab_register:
            st.markdown("")
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
                        st.session_state.logged_in = True
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.rerun()
                    else:
                        st.error(result["error"])


def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")

        is_admin = st.session_state.username == ADMIN_USERNAME

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("🎯 Interview", use_container_width=True):
                st.session_state.page = 'interview'
                st.rerun()
        with col_nav2:
            if st.button("📜 History", use_container_width=True):
                st.session_state.page = 'history'
                st.rerun()

        if is_admin:
            if st.button("🛠️ Admin Dashboard", use_container_width=True):
                st.session_state.page = 'admin'
                st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        if st.session_state.page == 'interview':
            render_interview_sidebar()


def render_interview_sidebar():
    st.header("📄 Interview Setup")

    quick_tab, full_tab = st.tabs(["⚡ Quick Start", "📄 Full Setup"])

    with quick_tab:
        st.markdown("*Enter a role to start instantly — no CV needed*")

        quick_role = st.text_input(
            "Job Role",
            value=st.session_state.quick_start_role,
            placeholder="e.g. Frontend Developer, Data Analyst..."
        )
        st.session_state.quick_start_role = quick_role

        seniority_q = st.selectbox(
            "Seniority Level",
            SENIORITY_LEVELS,
            index=SENIORITY_LEVELS.index(st.session_state.seniority),
            key="seniority_quick"
        )
        st.session_state.seniority = seniority_q

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            start_disabled = st.session_state.interview_started
            if st.button("▶️ Start", disabled=start_disabled, use_container_width=True, key="quick_start_btn"):
                role_value = quick_role.strip()
                if role_value:
                    st.session_state.setup_mode = 'quick'
                    st.session_state.cv_text = f"Role: {role_value}"
                    st.session_state.jd_text = f"{role_value} position"
                    start_interview()
                else:
                    st.warning("Please enter a job role first, then click Start again.")
        with col2:
            if st.button("🔄 Restart", use_container_width=True, key="quick_restart_btn"):
                reset_interview()
                st.rerun()

    with full_tab:
        st.markdown("*Upload your CV for tailored questions*")

        uploaded_file = st.file_uploader(
            "Upload CV/Resume (PDF, Word, TXT)",
            type=['pdf', 'docx', 'txt'],
            key='cv_upload'
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
            value=st.session_state.jd_text if st.session_state.setup_mode == 'full' else '',
            height=120,
            placeholder="Paste job requirements here..."
        )
        if jd_text:
            st.session_state.jd_text = jd_text

        st.divider()

        seniority_f = st.selectbox(
            "Seniority Level",
            SENIORITY_LEVELS,
            index=SENIORITY_LEVELS.index(st.session_state.seniority),
            key="seniority_full"
        )
        st.session_state.seniority = seniority_f

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            start_disabled = not st.session_state.cv_text or st.session_state.interview_started
            if st.button("▶️ Start", disabled=start_disabled, use_container_width=True, key="full_start_btn"):
                st.session_state.setup_mode = 'full'
                start_interview()
        with col2:
            if st.button("🔄 Restart", use_container_width=True, key="full_restart_btn"):
                reset_interview()
                st.rerun()

        if not st.session_state.cv_text:
            st.info("👆 Upload your CV to begin")


def start_interview():
    reset_interview()
    st.session_state.interview_started = True

    try:
        result = get_first_question(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority,
            demo_mode=False
        )

        greeting = result.get('greeting', 'Welcome to your mock interview!')
        first_question = result.get('question', 'Tell me about yourself.')

        full_message = f"{greeting}\n\n**Question 1/{TOTAL_QUESTIONS}:** {first_question}"

        st.session_state.messages.append({
            'role': 'assistant',
            'content': full_message
        })
        st.session_state.questions.append(first_question)
        st.session_state.current_question_index = 1
        st.session_state.awaiting_answer = True
        st.session_state.auto_speak_question = first_question

    except Exception as e:
        st.error(f"Failed to start interview: {str(e)}")
        st.session_state.interview_started = False


def process_answer(transcription: str):
    st.session_state.processing = True

    st.session_state.messages.append({
        'role': 'user',
        'content': transcription
    })
    st.session_state.answers.append(transcription)

    conversation_history = []
    for msg in st.session_state.messages[:-1]:
        conversation_history.append({
            'role': msg['role'],
            'content': msg['content']
        })

    try:
        result = evaluate_answer_and_get_next(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority,
            conversation_history,
            transcription,
            st.session_state.current_question_index,
            demo_mode=False
        )

        score = result.get('score', 5)
        justification = result.get('justification', '')
        pro_tip = result.get('pro_tip', '')
        next_question = result.get('next_question')

        st.session_state.scores.append(score)
        st.session_state.tips.append(pro_tip)
        st.session_state.justifications.append(justification)

        feedback_message = f"**Score: {score}/10**\n\n{justification}\n\n💡 **Pro Tip:** {pro_tip}"

        is_last_question = st.session_state.current_question_index >= TOTAL_QUESTIONS

        if not is_last_question:
            if not next_question:
                fallback_questions = [
                    "Can you describe a challenging technical problem you solved and what approach you took?",
                    "Tell me about a time you had to work under a tight deadline. How did you handle it?",
                    "What is your approach to learning new technologies or tools?",
                    "Describe a situation where you had a disagreement with a team member. How did you resolve it?",
                    "How do you prioritize tasks when you have multiple competing deadlines?"
                ]
                q_idx = st.session_state.current_question_index % len(fallback_questions)
                next_question = fallback_questions[q_idx]

            st.session_state.current_question_index += 1
            feedback_message += f"\n\n---\n\n**Next Question:**\n{next_question}"
            st.session_state.questions.append(next_question)
            st.session_state.awaiting_answer = True
            st.session_state.auto_speak_question = next_question
        else:
            st.session_state.interview_completed = True
            st.session_state.awaiting_answer = False
            feedback_message += "\n\n---\n\n🎉 **Interview Complete!** Click 'Generate Performance Report' below to get your detailed report."

        st.session_state.messages.append({
            'role': 'assistant',
            'content': feedback_message
        })

    except Exception as e:
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"⚠️ There was an error evaluating your response. Please try again.\n\nError: {str(e)}"
        })
        st.session_state.answers.pop()
        st.session_state.awaiting_answer = True

    finally:
        st.session_state.processing = False


def render_chat():
    question_idx = 0
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
            if message['role'] == 'assistant' and 'Question' in message['content']:
                if question_idx < len(st.session_state.questions):
                    q_text = st.session_state.questions[question_idx]
                    audio_key = f"tts_cache_{question_idx}"
                    if audio_key in st.session_state:
                        st.audio(st.session_state[audio_key], format="audio/wav")
                    else:
                        if st.button("🔊 Listen to Question", key=f"listen_{question_idx}"):
                            st.markdown("""
                            <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; margin-top: 4px;
                                background: rgba(59,95,192,0.06); border-radius: 8px;">
                                <div style="width: 8px; height: 8px; border-radius: 50%; background: #4a6fd0;
                                    animation: pulse 1s ease-in-out infinite alternate;"></div>
                                <span style="color: var(--text-loading); font-size: 0.9rem;">Generating audio...</span>
                            </div>
                            <style>@keyframes pulse { 0% { opacity: 0.3; } 100% { opacity: 1; } }</style>
                            """, unsafe_allow_html=True)
                            audio_bytes, error = text_to_speech(q_text)
                            if audio_bytes:
                                st.session_state[audio_key] = audio_bytes
                                st.rerun()
                            else:
                                st.error(f"Could not generate audio: {error}")
                    question_idx += 1

    if st.session_state.auto_speak_question:
        question_text = st.session_state.auto_speak_question
        st.session_state.auto_speak_question = ''
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; padding: 10px 14px;
            background: rgba(59,95,192,0.06); border-radius: 8px; margin: 8px 0;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #4a6fd0;
                animation: pulse 1s ease-in-out infinite alternate;"></div>
            <span style="color: var(--text-loading); font-size: 0.9rem;">Generating question audio...</span>
        </div>
        <style>@keyframes pulse { 0% { opacity: 0.3; } 100% { opacity: 1; } }</style>
        """, unsafe_allow_html=True)
        audio_bytes, error = text_to_speech(question_text)
        if audio_bytes:
            cache_idx = len(st.session_state.questions) - 1
            cache_key = f"tts_cache_{cache_idx}"
            st.session_state[cache_key] = audio_bytes
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            st.components.v1.html(
                f"""<script>
                (function() {{
                    var audio = new Audio("data:audio/wav;base64,{audio_b64}");
                    audio.play().catch(function() {{
                        document.addEventListener('click', function handler() {{
                            audio.play();
                            document.removeEventListener('click', handler);
                        }}, {{once: true}});
                    }});
                }})();
                </script>""",
                height=0
            )


def finish_interview_button(key: str):
    if st.button("🏁 Finish Interview", use_container_width=True, type="primary", key=key):
        st.session_state.interview_completed = True
        st.session_state.awaiting_answer = False
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"🎉 **Interview Finished!** You answered {len(st.session_state.answers)} out of {TOTAL_QUESTIONS} questions. Click 'Generate Performance Report' below to get your detailed report."
        })
        st.rerun()


def render_response_input():
    if st.session_state.processing:
        st.markdown("---")
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding: 20px; 
            background: linear-gradient(135deg, rgba(59,95,192,0.08), rgba(91,79,200,0.08)); 
            border: 1px solid rgba(120,100,200,0.15); border-radius: 12px; margin: 16px 0;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background: #4a6fd0; 
                animation: blink 1s ease-in-out infinite alternate;"></div>
            <span style="color: var(--text-loading); font-size: 1.1rem; font-weight: 500;">
                Processing your response... Please wait
            </span>
        </div>
        <style>
            @keyframes blink {
                0% { opacity: 0.3; transform: scale(0.8); }
                100% { opacity: 1; transform: scale(1.2); }
            }
        </style>
        """, unsafe_allow_html=True)
        return

    if not st.session_state.awaiting_answer:
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
    recorder_key = f"audio_recorder_{st.session_state.recorder_version}"

    import streamlit.components.v1 as components

    tab_audio, tab_text = st.tabs(["🎙️ Record Answer", "⌨️ Type Answer"])

    with tab_audio:
        mic_html = """
        <html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        @keyframes rippleOut {
            0% { transform: translate(-50%,-50%) scale(1); opacity: 0.5; }
            100% { transform: translate(-50%,-50%) scale(2.8); opacity: 0; }
        }
        @keyframes idlePulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(74,111,208,0.3); }
            50% { transform: scale(1.03); box-shadow: 0 0 20px 4px rgba(74,111,208,0.15); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(74,111,208,0.3); }
        }
        @keyframes recPulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255,60,60,0.4); }
            50% { transform: scale(1.08); box-shadow: 0 0 30px 10px rgba(255,60,60,0.2); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255,60,60,0.4); }
        }
        @keyframes fadeInUp {
            0% { opacity: 0; transform: translateY(6px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes textPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes dotBlink {
            0%, 20% { opacity: 0; }
            50% { opacity: 1; }
            100% { opacity: 0; }
        }
        .mic-container {
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; padding: 24px 16px 18px;
            background: linear-gradient(160deg, #3b5fc0 0%, #4a8bd4 45%, #5ba3e0 100%);
            border-radius: 16px; position: relative; overflow: hidden;
            transition: background 0.6s ease;
        }
        .mic-container.recording {
            background: linear-gradient(160deg, #1a3d8f 0%, #2558b0 45%, #3070c8 100%);
        }
        .rec-status {
            display: none; margin-bottom: 14px; text-align: center;
            animation: fadeInUp 0.4s ease-out;
        }
        .rec-status.visible { display: block; }
        .rec-status-text {
            color: #ff8a80; font-weight: 700; font-size: 16px;
            letter-spacing: 0.5px;
            text-shadow: 0 0 12px rgba(255,100,100,0.4);
            animation: textPulse 1.5s ease-in-out infinite;
        }
        .rec-status-text .dot {
            animation: dotBlink 1.4s ease-in-out infinite;
            font-size: 20px;
        }
        .rec-status-text .dot:nth-child(2) { animation-delay: 0.2s; }
        .rec-status-text .dot:nth-child(3) { animation-delay: 0.4s; }
        .rec-status-sub {
            color: rgba(255,255,255,0.7); font-size: 12px; margin-top: 4px;
        }
        .mic-circle-wrap {
            position: relative; width: 120px; height: 120px;
            display: flex; align-items: center; justify-content: center;
        }
        .ripple-ring {
            position: absolute; top: 50%; left: 50%;
            width: 90px; height: 90px; border-radius: 50%;
            transform: translate(-50%,-50%) scale(1);
            border: 2.5px solid rgba(255,70,70,0.5);
            opacity: 0; pointer-events: none;
        }
        .mic-circle {
            width: 84px; height: 84px; border-radius: 50%;
            background: radial-gradient(circle at 40% 35%, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0.05) 100%);
            display: flex; align-items: center; justify-content: center;
            position: relative; z-index: 2;
            animation: idlePulse 3s ease-in-out infinite;
            transition: background 0.4s ease;
        }
        .mic-circle.recording {
            background: radial-gradient(circle at 40% 35%, rgba(255,80,80,0.5) 0%, rgba(200,40,40,0.2) 60%, rgba(160,30,30,0.05) 100%);
            animation: recPulse 1.2s ease-in-out infinite;
        }
        .mic-circle svg {
            width: 40px; height: 40px; fill: white;
            transition: fill 0.3s ease;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }
        .mic-circle.recording svg { fill: #ff6b6b; }
        .mic-label {
            color: white; font-weight: 700; font-size: 15px;
            margin-top: 14px; text-align: center;
            text-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .mic-sublabel {
            color: rgba(255,255,255,0.7); font-size: 12px;
            margin-top: 4px; text-align: center;
        }
        </style></head><body>
        <div class="mic-container" id="mc">
            <div class="rec-status" id="recStatus">
                <div class="rec-status-text">
                    Recording<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span> Speak now
                </div>
                <div class="rec-status-sub">Click mic again to stop</div>
            </div>
            <div class="mic-circle-wrap">
                <div class="ripple-ring" id="r1"></div>
                <div class="ripple-ring" id="r2"></div>
                <div class="ripple-ring" id="r3"></div>
                <div class="mic-circle" id="micCircle">
                    <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                </div>
            </div>
            <div class="mic-label" id="micLabel">🎙️ Click the mic below to start</div>
            <div class="mic-sublabel" id="micSub">Speak your answer clearly</div>
        </div>
        <script>
        (function(){
            function detect() {
                var isRec = false;
                try {
                    var p = window.parent.document;
                    var ifs = p.querySelectorAll('iframe');
                    for (var i=0; i<ifs.length; i++) {
                        try {
                            var d = ifs[i].contentDocument || ifs[i].contentWindow.document;
                            if (!d) continue;
                            var svgs = d.querySelectorAll('svg');
                            for (var j=0; j<svgs.length; j++) {
                                var f = svgs[j].getAttribute('fill')||'';
                                if (f.indexOf('#e74c3c')!==-1||f==='red'){isRec=true;break;}
                            }
                        } catch(e){}
                        if(isRec) break;
                    }
                } catch(e){}
                var mc=document.getElementById('mc');
                var c=document.getElementById('micCircle');
                var r1=document.getElementById('r1');
                var r2=document.getElementById('r2');
                var r3=document.getElementById('r3');
                var lb=document.getElementById('micLabel');
                var sb=document.getElementById('micSub');
                var rs=document.getElementById('recStatus');
                if(!mc||!c) return;
                if(isRec){
                    mc.classList.add('recording');
                    c.classList.add('recording');
                    if(rs) rs.classList.add('visible');
                    if(r1){r1.style.animation='rippleOut 1.6s ease-out infinite';}
                    if(r2){r2.style.animation='rippleOut 1.6s ease-out 0.5s infinite';}
                    if(r3){r3.style.animation='rippleOut 1.6s ease-out 1.0s infinite';}
                    if(lb) lb.style.display='none';
                    if(sb) sb.style.display='none';
                } else {
                    mc.classList.remove('recording');
                    c.classList.remove('recording');
                    if(rs) rs.classList.remove('visible');
                    if(r1){r1.style.animation='none';r1.style.opacity='0';}
                    if(r2){r2.style.animation='none';r2.style.opacity='0';}
                    if(r3){r3.style.animation='none';r3.style.opacity='0';}
                    if(lb) lb.style.display='block';
                    if(sb) sb.style.display='block';
                }
            }
            setInterval(detect, 300);
        })();
        </script>
        </body></html>
        """
        components.html(mic_html, height=230)

        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#4a6fd0",
            icon_size="2x",
            pause_threshold=30.0,
            key=recorder_key
        )

        if audio_bytes:
            st.session_state.recorded_audio = audio_bytes
            st.session_state.has_recording = True

        if st.session_state.has_recording and st.session_state.get('recorded_audio'):
            stored_audio = st.session_state.recorded_audio

            st.markdown("""
            <div style="background: rgba(39,174,96,0.08); border: 1px solid rgba(39,174,96,0.2); 
                border-radius: 12px; padding: 12px 16px; margin: 12px 0;">
                <span style="color: #27ae60; font-weight: 600;">✅ Recording captured!</span>
                <span style="color: var(--text-secondary);"> Preview below, then submit or re-record.</span>
            </div>
            """, unsafe_allow_html=True)

            st.audio(stored_audio, format="audio/wav")

            if st.button("🎤 Submit Audio Answer", type="primary", use_container_width=True,
                         key=f"audio_submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}"):
                st.session_state.processing = True
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 12px; padding: 16px; 
                    background: linear-gradient(135deg, rgba(59,95,192,0.08), rgba(91,79,200,0.08)); 
                    border: 1px solid rgba(120,100,200,0.15); border-radius: 12px; margin: 8px 0;">
                    <div style="width: 10px; height: 10px; border-radius: 50%; background: #4a6fd0; 
                        animation: pulse 1s ease-in-out infinite alternate;"></div>
                    <span style="color: var(--text-loading); font-weight: 500;">
                        Transcribing and evaluating your response...
                    </span>
                </div>
                <style>@keyframes pulse { 0% { opacity: 0.3; } 100% { opacity: 1; } }</style>
                """, unsafe_allow_html=True)
                transcribed_text, error = speech_to_text(stored_audio)
                if error:
                    st.session_state.processing = False
                    st.error(f"Could not transcribe audio: {error}")
                elif transcribed_text:
                    st.info(f"**Transcribed:** {transcribed_text}")
                    st.session_state.has_recording = False
                    st.session_state.recorded_audio = None
                    process_answer(transcribed_text)
                    st.rerun()
                else:
                    st.session_state.processing = False
                    st.warning("No speech detected. Please try recording again.")

            if st.button("🔄 Re-record", use_container_width=True,
                         key=f"rerecord_{st.session_state.current_question_index}_{len(st.session_state.answers)}"):
                st.session_state.recorder_version += 1
                st.session_state.has_recording = False
                st.session_state.recorded_audio = None
                st.rerun()

        if len(st.session_state.answers) >= 1:
            finish_interview_button(f"finish_audio_{st.session_state.current_question_index}")

    with tab_text:
        text_answer = st.text_area(
            "Type your answer here",
            key=answer_key,
            height=200,
            placeholder="Take your time and provide a detailed response..."
        )

        submit_key = f"submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}"

        if st.button("📝 Submit Text Answer", type="primary", key=submit_key, use_container_width=True):
            if text_answer.strip():
                st.session_state.processing = True
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 10px; padding: 12px 16px; margin-top: 8px;
                    background: linear-gradient(135deg, rgba(59,95,192,0.08), rgba(91,79,200,0.08));
                    border: 1px solid rgba(120,100,200,0.15); border-radius: 10px;">
                    <div style="width: 10px; height: 10px; border-radius: 50%; background: #4a6fd0;
                        animation: pulse 1s ease-in-out infinite alternate;"></div>
                    <span style="color: var(--text-loading); font-weight: 500;">Evaluating your response...</span>
                </div>
                <style>@keyframes pulse { 0% { opacity: 0.3; } 100% { opacity: 1; } }</style>
                """, unsafe_allow_html=True)
                process_answer(text_answer)
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
        <div style="background: linear-gradient(135deg, rgba(59,95,192,0.06), rgba(91,79,200,0.06)); 
            border: 1px solid rgba(120,100,200,0.12); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
            <h2 style="color: var(--text-hero-title); margin: 0 0 8px 0;">📋 Your Interview Performance Report</h2>
            <p style="color: var(--text-secondary); margin: 0;">Personalized analysis based on your interview</p>
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
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; padding: 14px 18px; margin-top: 8px;
            background: linear-gradient(135deg, rgba(59,95,192,0.08), rgba(91,79,200,0.08));
            border: 1px solid rgba(120,100,200,0.15); border-radius: 10px;">
            <div style="width: 10px; height: 10px; border-radius: 50%; background: #4a6fd0;
                animation: pulse 1s ease-in-out infinite alternate;"></div>
            <span style="color: var(--text-loading); font-weight: 500;">Analyzing your interview performance...</span>
        </div>
        <style>@keyframes pulse { 0% { opacity: 0.3; } 100% { opacity: 1; } }</style>
        """, unsafe_allow_html=True)
        try:
            report = generate_final_report(
                st.session_state.cv_text,
                st.session_state.jd_text,
                st.session_state.seniority,
                st.session_state.questions,
                st.session_state.answers,
                st.session_state.scores,
                st.session_state.tips,
                demo_mode=False
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
                avg_score=avg_score
            )

            st.rerun()

        except Exception as e:
            st.error(f"Failed to generate report: {str(e)}")


def get_user_timezone():
    if 'user_tz' not in st.session_state:
        st.session_state.user_tz = None

    if st.session_state.user_tz is None:
        tz_param = st.query_params.get("tz")
        if tz_param:
            st.session_state.user_tz = tz_param
        else:
            st.components.v1.html("""
            <script>
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const url = new URL(window.parent.location);
            if (!url.searchParams.has('tz')) {
                url.searchParams.set('tz', tz);
                window.parent.history.replaceState({}, '', url);
                window.parent.location.reload();
            }
            </script>
            """, height=0)
            return None

    return st.session_state.user_tz


def format_interview_time(dt, tz_name):
    if not dt:
        return "Unknown"
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        user_tz = ZoneInfo(tz_name)
        local_dt = dt.astimezone(user_tz)
        return local_dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return dt.strftime("%B %d, %Y at %I:%M %p")


def render_history_page():
    st.title("📜 Interview History")
    st.markdown(f'<p style="color: var(--text-secondary);">Past interviews for <strong style="color: var(--text-accent);">{st.session_state.username}</strong></p>', unsafe_allow_html=True)
    st.markdown("---")

    user_tz = get_user_timezone()

    interviews = get_user_interviews(st.session_state.user_id)

    if not interviews:
        st.info("No interviews yet. Go to the Interview page to start your first one!")
        return

    for i, interview in enumerate(interviews):
        created = format_interview_time(interview["created_at"], user_tz) if user_tz else (interview["created_at"].strftime("%B %d, %Y at %I:%M %p") if interview["created_at"] else "Unknown")
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

            if interview["report"]:
                st.markdown("### 📋 Feedback Report")
                st.markdown(interview["report"])


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

    from datetime import datetime, timedelta, timezone as tz_module
    now_utc = datetime.now(tz_module.utc)
    week_ago = now_utc - timedelta(days=7)
    interviews_this_week = sum(
        1 for iv in all_interviews
        if iv["created_at"] and (
            iv["created_at"].replace(tzinfo=tz_module.utc) if iv["created_at"].tzinfo is None else iv["created_at"]
        ) >= week_ago
    )

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
        if iv["created_at"]:
            dt = iv["created_at"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz_module.utc)
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
            if iv["created_at"] and iv["avg_score"] is not None:
                dt = iv["created_at"]
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tz_module.utc)
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
        user_rows.append({
            "Username": u["username"],
            "Joined": u["created_at"].strftime("%Y-%m-%d") if u["created_at"] else "",
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
        created_str = iv["created_at"].strftime("%Y-%m-%d %H:%M") if iv["created_at"] else "Unknown"
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
            summary_rows.append({
                "interview_id": iv["id"],
                "username": iv["username"],
                "date": iv["created_at"].strftime("%Y-%m-%d %H:%M") if iv["created_at"] else "",
                "seniority": iv["seniority"],
                "avg_score": iv["avg_score"],
                "performance": "Excellent" if (iv["avg_score"] or 0) >= 8 else "Good" if (iv["avg_score"] or 0) >= 6 else "Needs Work",
                "role": (iv.get("cv_text") or "").replace("Role: ", "").strip() if (iv.get("cv_text") or "").startswith("Role: ") else "Custom CV",
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
            questions = iv["questions"] or []
            answers = iv["answers"] or []
            scores = iv["scores"] or []
            tips = iv["tips"] or []
            for j in range(len(questions)):
                qa_rows.append({
                    "interview_id": iv["id"],
                    "username": iv["username"],
                    "date": iv["created_at"].strftime("%Y-%m-%d %H:%M") if iv["created_at"] else "",
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

    if not st.session_state.interview_started:
        st.markdown("---")

        st.markdown("""
        <div class="hero-card">
            <h3 style="color: var(--text-hero-title) !important; margin-top: 0;">Welcome! 👋</h3>
            <p style="color: var(--text-hero-body);">Get ready to ace your next interview with personalized AI coaching.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **How it works:**
            1. ⚡ **Quick Start**: Enter a role + seniority in the sidebar
            2. *Or* 📄 **Full Setup**: Upload CV + job description
            3. ▶️ Click "Start" to begin
            4. ✍️ Answer the interview question
            5. 📊 Get instant feedback and a final report
            """)
        with col2:
            st.markdown("""
            **Features:**
            - ⚡ **Quick Start**: No CV needed — just pick a role
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
        layout="wide"
    )

    inject_custom_css()
    init_db()
    init_session_state()

    if not st.session_state.logged_in:
        render_auth_page()
        return

    render_sidebar()

    if st.session_state.page == 'history':
        render_history_page()
    elif st.session_state.page == 'admin' and st.session_state.username == ADMIN_USERNAME:
        render_admin_page()
    else:
        render_interview_page()


if __name__ == "__main__":
    main()
