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

from config import SENIORITY_LEVELS, TOTAL_QUESTIONS
from utils.pdf_parser import parse_document
from utils.voice import speech_to_text, text_to_speech
from utils.interview_engine import (
    get_first_question,
    evaluate_answer_and_get_next,
    generate_final_report
)
from utils.db import init_db, create_user, verify_user, save_interview, get_user_interviews


def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        25% { background-position: 50% 100%; }
        50% { background-position: 100% 50%; }
        75% { background-position: 50% 0%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(135deg, #0a1628, #0d2137, #0f2b4a, #0a1f3d, #081a30);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }

    @keyframes sidebarGlow {
        0% { background-position: 0% 0%; }
        50% { background-position: 100% 100%; }
        100% { background-position: 0% 0%; }
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1a2e, #0f2540, #112d4e, #0d2137);
        background-size: 200% 200%;
        animation: sidebarGlow 12s ease infinite;
        border-right: 1px solid rgba(100,180,255,0.1);
    }

    [data-testid="stSidebar"] * {
        color: #d0e4f7 !important;
    }

    @keyframes titleGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    h1 {
        background: linear-gradient(90deg, #4fc3f7, #29b6f6, #81d4fa, #03a9f4, #4dd0e1, #4fc3f7);
        background-size: 300% 100%;
        animation: titleGlow 6s ease infinite;
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
        color: #b0d4f1 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(100,180,255,0.06);
        border-radius: 12px;
        padding: 6px;
    }

    .stTabs [data-baseweb="tab-list"] button {
        flex: 1;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8bb8d9 !important;
        font-weight: 500;
        padding: 10px 24px;
        width: 100%;
        justify-content: center;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1976d2, #0288d1) !important;
        color: white !important;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1976d2 0%, #0288d1 50%, #0097a7 100%) !important;
        background-size: 200% 200%;
        animation: gradientShift 8s ease infinite;
        color: white !important;
        box-shadow: 0 4px 15px rgba(25, 118, 210, 0.4);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 25px rgba(25, 118, 210, 0.6);
        transform: translateY(-1px);
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(100,180,255,0.08) !important;
        color: #b0d4f1 !important;
        border: 1px solid rgba(100,180,255,0.2) !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(100,180,255,0.15) !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(100,180,255,0.06) !important;
        border: 1px solid rgba(100,180,255,0.15) !important;
        border-radius: 10px !important;
        color: #d0e4f7 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #29b6f6 !important;
        box-shadow: 0 0 10px rgba(41, 182, 246, 0.3) !important;
    }

    .stSelectbox > div > div {
        background: rgba(100,180,255,0.06) !important;
        border: 1px solid rgba(100,180,255,0.15) !important;
        border-radius: 10px !important;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(25,118,210,0.12), rgba(2,136,209,0.12));
        border: 1px solid rgba(41,182,246,0.25);
        border-radius: 12px;
        padding: 16px;
    }

    [data-testid="stMetric"] label {
        color: #8bb8d9 !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #4fc3f7 !important;
        font-weight: 700 !important;
    }

    [data-testid="stExpander"] {
        background: rgba(100,180,255,0.04);
        border: 1px solid rgba(100,180,255,0.1);
        border-radius: 12px;
    }

    [data-testid="stChatMessage"] {
        background: rgba(100,180,255,0.04) !important;
        border: 1px solid rgba(100,180,255,0.08) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
    }

    .stMarkdown p, .stMarkdown li {
        color: #b8d4ea;
    }

    .stAlert > div {
        border-radius: 10px !important;
    }

    [data-testid="stFileUploader"] {
        background: rgba(100,180,255,0.04);
        border: 1px dashed rgba(41,182,246,0.4);
        border-radius: 12px;
        padding: 8px;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(25,118,210,0.1), rgba(2,136,209,0.1));
        border: 1px solid rgba(41,182,246,0.2);
        border-radius: 16px;
        padding: 32px;
        margin: 16px 0;
    }

    .stat-pill {
        display: inline-block;
        background: linear-gradient(135deg, #1976d2, #0288d1);
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 2px 4px;
    }

    hr {
        border-color: rgba(100,180,255,0.1) !important;
    }

    .stDivider {
        border-color: rgba(100,180,255,0.1) !important;
    }

    [data-testid="stSidebar"] .stDivider hr,
    [data-testid="stSidebar"] hr {
        border-color: rgba(100,180,255,0.15) !important;
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
        st.markdown('<p style="color: #8bb8d9; font-size: 1.2rem; margin-bottom: 24px;">Master your next job interview with AI-powered coaching</p>', unsafe_allow_html=True)

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

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("🎯 Interview", use_container_width=True):
                st.session_state.page = 'interview'
                st.rerun()
        with col_nav2:
            if st.button("📜 History", use_container_width=True):
                st.session_state.page = 'history'
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
        value=st.session_state.jd_text,
        height=120,
        placeholder="Paste job requirements here..."
    )
    st.session_state.jd_text = jd_text

    st.divider()

    seniority = st.selectbox(
        "Seniority Level",
        SENIORITY_LEVELS,
        index=SENIORITY_LEVELS.index(st.session_state.seniority)
    )
    st.session_state.seniority = seniority

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        start_disabled = not st.session_state.cv_text or st.session_state.interview_started
        if st.button("▶️ Start", disabled=start_disabled, use_container_width=True):
            start_interview()

    with col2:
        if st.button("🔄 Restart", use_container_width=True):
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

        full_message = f"{greeting}\n\n**Question 1/{TOTAL_QUESTIONS}:**\n{first_question}"

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
                    "Describe a situation where you had a disagreement with a team member. How did you resolve it?"
                ]
                q_idx = st.session_state.current_question_index % len(fallback_questions)
                next_question = fallback_questions[q_idx]

            st.session_state.current_question_index += 1
            feedback_message += f"\n\n---\n\n**Question {st.session_state.current_question_index}/{TOTAL_QUESTIONS}:**\n{next_question}"
            st.session_state.questions.append(next_question)
            st.session_state.awaiting_answer = True
            st.session_state.auto_speak_question = next_question
        else:
            st.session_state.interview_completed = True
            st.session_state.awaiting_answer = False
            feedback_message += "\n\n---\n\n🎉 **Interview Complete!** Click 'Generate Feedback' below to get your detailed report."

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
                            with st.spinner("Generating audio..."):
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
        with st.spinner("Generating question audio..."):
            audio_bytes, error = text_to_speech(question_text)
            if audio_bytes:
                cache_idx = len(st.session_state.questions) - 1
                cache_key = f"tts_cache_{cache_idx}"
                st.session_state[cache_key] = audio_bytes
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                st.components.v1.html(
                    f'<audio autoplay src="data:audio/wav;base64,{audio_b64}"></audio>',
                    height=0
                )


def render_response_input():
    if st.session_state.processing:
        st.markdown("---")
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding: 20px; 
            background: linear-gradient(135deg, rgba(25,118,210,0.15), rgba(2,136,209,0.15)); 
            border: 1px solid rgba(41,182,246,0.3); border-radius: 12px; margin: 16px 0;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background: #29b6f6; 
                animation: blink 1s ease-in-out infinite alternate;"></div>
            <span style="color: #b0d4f1; font-size: 1.1rem; font-weight: 500;">
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
    st.markdown(f"### ✍️ Your Response — Question {st.session_state.current_question_index} of {TOTAL_QUESTIONS}")

    answer_key = f"answer_{st.session_state.current_question_index}_{len(st.session_state.answers)}"
    recorder_key = f"audio_{st.session_state.current_question_index}_{len(st.session_state.answers)}_{st.session_state.recorder_version}"

    tab_voice, tab_type = st.tabs(["🎙️ Record Answer", "⌨️ Type Answer"])

    with tab_type:
        text_answer = st.text_area(
            "Type your answer here",
            key=answer_key,
            height=150,
            placeholder="Take your time and provide a detailed response..."
        )

        submit_key = f"submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}"

        if st.button("📤 Submit Answer", type="primary", key=submit_key):
            if text_answer.strip():
                with st.spinner("Evaluating your response..."):
                    process_answer(text_answer)
                st.rerun()
            else:
                st.warning("Please enter your answer before submitting.")

    with tab_voice:
        st.markdown('<p style="color: #c3cfe2; margin-bottom: 4px;">Click the microphone to record (up to 30 seconds). Click again to stop.</p>', unsafe_allow_html=True)

        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#b0d4f1",
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
            <div style="background: rgba(39,174,96,0.1); border: 1px solid rgba(39,174,96,0.3); 
                border-radius: 10px; padding: 12px; margin: 8px 0;">
                <span style="color: #27ae60; font-weight: 600;">✅ Recording captured!</span>
                <span style="color: #8bb8d9;"> Preview below, then submit or re-record.</span>
            </div>
            """, unsafe_allow_html=True)

            st.audio(stored_audio, format="audio/wav")

            col_submit, col_rerecord = st.columns(2)
            with col_submit:
                if st.button("📤 Submit Audio Answer", type="primary", use_container_width=True,
                             key=f"audio_submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}"):
                    st.session_state.processing = True
                    st.markdown("""
                    <div style="display: flex; align-items: center; gap: 12px; padding: 16px; 
                        background: linear-gradient(135deg, rgba(25,118,210,0.15), rgba(2,136,209,0.15)); 
                        border: 1px solid rgba(41,182,246,0.3); border-radius: 12px; margin: 8px 0;">
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: #29b6f6; 
                            animation: pulse 1s ease-in-out infinite alternate;"></div>
                        <span style="color: #b0d4f1; font-weight: 500;">
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
            with col_rerecord:
                if st.button("🔄 Re-record", use_container_width=True,
                             key=f"rerecord_{st.session_state.current_question_index}_{len(st.session_state.answers)}"):
                    st.session_state.recorder_version += 1
                    st.session_state.has_recording = False
                    st.session_state.recorded_audio = None
                    st.rerun()
        else:
            st.markdown("""
            <div style="color: #8bb8d9; font-size: 0.9rem; padding: 8px 0;">
                🎙️ Press the microphone above to start. The button turns 
                <span style="color: #e74c3c; font-weight: 600;">red</span> while recording.
            </div>
            """, unsafe_allow_html=True)

            st.button("📤 Submit Audio Answer", type="primary", use_container_width=True, disabled=True,
                      key=f"audio_submit_disabled_{st.session_state.current_question_index}_{len(st.session_state.answers)}")


def render_final_report():
    if not st.session_state.interview_completed:
        return

    st.markdown("---")

    if st.session_state.report_generated:
        avg_score = sum(st.session_state.scores) / len(st.session_state.scores)

        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(25,118,210,0.12), rgba(2,136,209,0.12)); 
            border: 1px solid rgba(41,182,246,0.3); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
            <h2 style="color: #e0e0f0; margin: 0 0 8px 0;">📋 Your Interview Performance Report</h2>
            <p style="color: #8bb8d9; margin: 0;">Personalized analysis based on your interview</p>
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
        with st.spinner("Analyzing your interview performance..."):
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
    st.markdown(f'<p style="color: #8bb8d9;">Past interviews for <strong style="color:#4fc3f7;">{st.session_state.username}</strong></p>', unsafe_allow_html=True)
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


def render_interview_page():
    st.markdown('<h1 style="margin-bottom: 0;"><span style="font-size: 1.1em;">🎯</span> AI Mock Interview</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #8bb8d9; font-size: 1.1rem;">Practice your interview skills with AI-powered coaching</p>', unsafe_allow_html=True)

    if not st.session_state.interview_started:
        st.markdown("---")

        st.markdown("""
        <div class="hero-card">
            <h3 style="color: #e0e0e0 !important; margin-top: 0;">Welcome! 👋</h3>
            <p style="color: #c3cfe2;">Get ready to ace your next interview with personalized AI coaching.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **How it works:**
            1. 📄 Upload your CV/Resume in the sidebar
            2. 📝 Optionally paste the job description
            3. ▶️ Click "Start" to begin
            4. ✍️ Answer the interview question
            5. 📊 Get instant feedback and a final report
            """)
        with col2:
            st.markdown("""
            **Features:**
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
    else:
        render_interview_page()


if __name__ == "__main__":
    main()
