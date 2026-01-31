"""
AI Mock Interview Platform
Main Streamlit application with voice-enabled interview functionality.
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from config import SENIORITY_LEVELS, TOTAL_QUESTIONS
from utils.pdf_parser import parse_document
from utils.voice import text_to_speech, speech_to_text, play_audio
from utils.interview_engine import (
    get_first_question,
    evaluate_answer_and_get_next,
    generate_final_report
)


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
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
        'voice_enabled': True,
        'seniority': 'Mid',
        'current_audio': None,
        'awaiting_answer': False,
        'last_transcription': '',
        'show_transcription': False,
        'processing': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_interview():
    """Reset all interview-related session state."""
    st.session_state.messages = []
    st.session_state.current_question_index = 0
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.scores = []
    st.session_state.tips = []
    st.session_state.justifications = []
    st.session_state.interview_started = False
    st.session_state.interview_completed = False
    st.session_state.current_audio = None
    st.session_state.awaiting_answer = False
    st.session_state.last_transcription = ''
    st.session_state.show_transcription = False
    st.session_state.processing = False


def render_sidebar():
    """Render the sidebar with user inputs."""
    with st.sidebar:
        st.header("📄 Interview Setup")
        
        st.subheader("Upload Your CV/Resume")
        uploaded_file = st.file_uploader(
            "Supported formats: PDF, Word (.docx), Text (.txt)",
            type=['pdf', 'docx', 'txt'],
            key='cv_upload'
        )
        
        if uploaded_file:
            cv_text, error = parse_document(uploaded_file)
            if error:
                st.error(f"⚠️ {error}")
                st.info("💡 Tips:\n- Ensure your PDF has selectable text (not scanned images)\n- Try saving as .docx or .txt if issues persist")
            else:
                st.session_state.cv_text = cv_text
                st.success(f"✅ CV loaded ({len(cv_text.split())} words)")
        
        st.divider()
        
        st.subheader("Job Description (Optional)")
        jd_text = st.text_area(
            "Paste the job description here",
            value=st.session_state.jd_text,
            height=150,
            placeholder="Paste job requirements, responsibilities, and qualifications..."
        )
        st.session_state.jd_text = jd_text
        
        st.divider()
        
        st.subheader("Settings")
        seniority = st.selectbox(
            "Seniority Level",
            SENIORITY_LEVELS,
            index=SENIORITY_LEVELS.index(st.session_state.seniority)
        )
        st.session_state.seniority = seniority
        
        voice_enabled = st.toggle("🔊 Voice Mode", value=st.session_state.voice_enabled)
        st.session_state.voice_enabled = voice_enabled
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_disabled = not st.session_state.cv_text or st.session_state.interview_started
            if st.button("▶️ Start Interview", disabled=start_disabled, use_container_width=True):
                start_interview()
        
        with col2:
            if st.button("🔄 Restart", use_container_width=True):
                reset_interview()
                st.rerun()
        
        if not st.session_state.cv_text:
            st.info("👆 Please upload your CV to begin")
        
        st.divider()
        st.caption("💡 **Tips:**\n- Speak clearly when recording\n- Take your time to think\n- Be specific with examples")


def start_interview():
    """Initialize and start the interview."""
    reset_interview()
    st.session_state.interview_started = True
    
    try:
        result = get_first_question(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority
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
        
        if st.session_state.voice_enabled:
            audio_bytes, error = text_to_speech(full_message.replace('**', '').replace('\n\n', '. '))
            if not error:
                st.session_state.current_audio = audio_bytes
        
    except Exception as e:
        st.error(f"Failed to start interview: {str(e)}")
        st.session_state.interview_started = False


def process_answer(transcription: str):
    """Process the user's answer and get AI feedback."""
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
            st.session_state.current_question_index
        )
        
        score = result.get('score', 5)
        justification = result.get('justification', '')
        pro_tip = result.get('pro_tip', '')
        next_question = result.get('next_question')
        
        st.session_state.scores.append(score)
        st.session_state.tips.append(pro_tip)
        st.session_state.justifications.append(justification)
        
        feedback_message = f"**Score: {score}/10**\n\n{justification}\n\n💡 **Pro Tip:** {pro_tip}"
        
        if next_question and st.session_state.current_question_index < TOTAL_QUESTIONS:
            st.session_state.current_question_index += 1
            feedback_message += f"\n\n---\n\n**Question {st.session_state.current_question_index}/{TOTAL_QUESTIONS}:**\n{next_question}"
            st.session_state.questions.append(next_question)
            st.session_state.awaiting_answer = True
        else:
            st.session_state.interview_completed = True
            st.session_state.awaiting_answer = False
            feedback_message += "\n\n---\n\n🎉 **Interview Complete!** Click 'Generate Feedback' below to get your detailed report."
        
        st.session_state.messages.append({
            'role': 'assistant',
            'content': feedback_message
        })
        
        if st.session_state.voice_enabled:
            speak_text = feedback_message.replace('**', '').replace('💡', '').replace('🎉', '').replace('---', '')
            audio_bytes, error = text_to_speech(speak_text)
            if not error:
                st.session_state.current_audio = audio_bytes
        
    except Exception as e:
        st.error(f"Error processing answer: {str(e)}")
    
    st.session_state.processing = False
    st.session_state.show_transcription = False
    st.session_state.last_transcription = ''


def render_chat():
    """Render the chat interface."""
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])


def render_audio_controls():
    """Render audio recording and playback controls."""
    if not st.session_state.awaiting_answer or st.session_state.processing:
        return
    
    st.markdown("---")
    
    if st.session_state.current_audio and st.session_state.voice_enabled:
        st.markdown("#### 🔊 Listen to the question:")
        st.audio(st.session_state.current_audio, format="audio/wav", autoplay=True)
        st.session_state.current_audio = None
    
    st.markdown("### 🎤 Your Response")
    st.markdown(f"**Question {st.session_state.current_question_index} of {TOTAL_QUESTIONS}**")
    
    recorder_key = f"recorder_q{st.session_state.current_question_index}_{len(st.session_state.answers)}"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        audio_bytes = audio_recorder(
            text="Click to record your answer",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_size="2x",
            pause_threshold=2.0,
            key=recorder_key
        )
    
    with col2:
        st.markdown("")
        st.caption("🎙️ Click mic to record")
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        if not st.session_state.show_transcription:
            with st.spinner("Transcribing your answer..."):
                transcription, error = speech_to_text(audio_bytes)
                
                if error:
                    st.error(f"⚠️ {error}")
                    st.info("Please try recording again or use text input below.")
                else:
                    st.session_state.last_transcription = transcription
                    st.session_state.show_transcription = True
                    st.rerun()
    
    if st.session_state.show_transcription and st.session_state.last_transcription:
        st.markdown("**Your transcribed answer:**")
        st.info(st.session_state.last_transcription)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Submit Answer", type="primary", use_container_width=True):
                process_answer(st.session_state.last_transcription)
                st.rerun()
        with col2:
            if st.button("🔄 Re-record", use_container_width=True):
                st.session_state.show_transcription = False
                st.session_state.last_transcription = ''
                st.rerun()
    
    st.markdown("---")
    st.markdown("##### 📝 Or type your answer:")
    text_answer = st.text_area(
        "Type your response here",
        key=f"text_answer_q{st.session_state.current_question_index}_{len(st.session_state.answers)}",
        height=100,
        placeholder="If you can't use the microphone, type your answer here..."
    )
    if text_answer and st.button("📤 Submit Text Answer", key=f"submit_text_{st.session_state.current_question_index}"):
        process_answer(text_answer)
        st.rerun()


def render_final_report():
    """Render the final feedback report section."""
    if st.session_state.interview_completed:
        st.markdown("---")
        
        if st.button("📊 Generate Feedback Report", type="primary", use_container_width=True):
            with st.spinner("Generating your personalized feedback report..."):
                try:
                    report = generate_final_report(
                        st.session_state.cv_text,
                        st.session_state.jd_text,
                        st.session_state.seniority,
                        st.session_state.questions,
                        st.session_state.answers,
                        st.session_state.scores,
                        st.session_state.tips
                    )
                    
                    st.markdown("## 📋 Your Interview Feedback Report")
                    
                    avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Average Score", f"{avg_score:.1f}/10")
                    with cols[1]:
                        st.metric("Questions Answered", len(st.session_state.answers))
                    with cols[2]:
                        performance = "Excellent" if avg_score >= 8 else "Good" if avg_score >= 6 else "Needs Work"
                        st.metric("Performance", performance)
                    
                    st.markdown("---")
                    st.markdown(report)
                    
                except Exception as e:
                    st.error(f"Failed to generate report: {str(e)}")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="AI Mock Interview",
        page_icon="🎯",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("🎯 AI Mock Interview Platform")
    st.markdown("Practice your interview skills with an AI interviewer that speaks and listens!")
    
    render_sidebar()
    
    if not st.session_state.interview_started:
        st.markdown("---")
        st.markdown("""
        ### Welcome! 👋
        
        This AI-powered mock interview platform will help you practice for your next job interview.
        
        **How it works:**
        1. 📄 Upload your CV/Resume in the sidebar
        2. 📝 Optionally paste the job description
        3. ▶️ Click "Start Interview" to begin
        4. 🎤 Answer questions using voice recording
        5. 📊 Get instant feedback and a final report
        
        **Features:**
        - 🔊 **Voice Mode**: AI speaks questions, you answer by voice
        - 📈 **Instant Scoring**: Get scored 0-10 on each answer
        - 💡 **Pro Tips**: Actionable advice after each response
        - 📋 **Final Report**: Comprehensive feedback with practice plan
        """)
    else:
        render_chat()
        render_audio_controls()
        render_final_report()


if __name__ == "__main__":
    main()
