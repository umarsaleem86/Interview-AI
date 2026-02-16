"""
Interview engine for managing AI-powered mock interviews.
Handles OpenAI API calls, prompt building, and interview logic.
Uses Replit AI Integrations for OpenAI access.
"""

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI

from config import OPENAI_MODEL, TOTAL_QUESTIONS, DEMO_MODE


def get_openai_client() -> OpenAI:
    """
    Get OpenAI client configured for Replit AI Integrations.
    This uses Replit's AI Integrations service, which provides OpenAI-compatible 
    API access without requiring your own OpenAI API key.
    """
    return OpenAI(
        api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    )


def build_system_prompt(cv_text: str, jd_text: str, seniority: str) -> str:
    """
    Build the system prompt for the AI interviewer.
    
    Args:
        cv_text: Extracted text from CV/resume
        jd_text: Job description text
        seniority: Candidate seniority level
        
    Returns:
        System prompt string
    """
    return f"""You are an expert technical interviewer conducting a mock interview for a {seniority}-level position.

CANDIDATE'S CV/RESUME:
{cv_text}

JOB DESCRIPTION/REQUIREMENTS:
{jd_text if jd_text else "General software engineering role - focus on the candidate's background and experience from their CV."}

YOUR ROLE:
- You will ask exactly {TOTAL_QUESTIONS} interview questions tailored to the job requirements and candidate's background.
- Ask only ONE question at a time.
- CRITICAL: Keep each question SHORT and CONCISE — maximum 1-2 sentences. Do NOT ask multi-part questions. Ask one simple, clear question that can be answered in a few minutes.
- After each candidate answer, you MUST respond with a JSON object containing:
  1. "score": A number from 0-10 rating the answer
  2. "justification": One sentence explaining the score
  3. "pro_tip": A short, actionable tip to improve their answer
  4. "next_question": The next interview question (if questions remain) or null if this was the last question
  5. "question_number": The number of the question just answered

IMPORTANT RULES:
- Be encouraging but honest in your feedback
- Pro tips should be specific and actionable
- Questions should be relevant to both the CV and job requirements
- Keep questions brief and focused — never combine multiple questions into one
- After question {TOTAL_QUESTIONS}, set next_question to null to signal the interview is complete

RESPONSE FORMAT (strict JSON):
{{
    "score": <0-10>,
    "justification": "<one sentence>",
    "pro_tip": "<actionable advice>",
    "next_question": "<next question or null>",
    "question_number": <number>
}}"""


def get_demo_first_question() -> Dict:
    """Return a mock first question for demo mode."""
    return {
        "greeting": "Welcome to your demo interview! This is a test mode that doesn't use AI credits.",
        "question": "Tell me about a recent project you worked on and what your role was in it."
    }


def get_demo_evaluation(question_number: int, answer: str) -> Dict:
    """Return mock evaluation for demo mode."""
    demo_scores = [7, 8]
    demo_tips = [
        "Try to quantify your achievements with specific numbers or metrics.",
        "Use the STAR method (Situation, Task, Action, Result) for behavioral questions."
    ]
    demo_next_questions = [
        "What was the biggest challenge you faced in that project and how did you overcome it?",
        None
    ]
    
    idx = min(question_number - 1, len(demo_scores) - 1)
    
    return {
        "score": demo_scores[idx],
        "justification": f"Good answer! You provided relevant details about your experience. (Demo mode - score is simulated)",
        "pro_tip": demo_tips[idx],
        "next_question": demo_next_questions[idx] if question_number < TOTAL_QUESTIONS else None,
        "question_number": question_number
    }


def get_demo_final_report(scores: List[int]) -> str:
    """Return a mock final report for demo mode."""
    avg_score = sum(scores) / len(scores) if scores else 5
    return f"""## Interview Feedback Report (Demo Mode)

### Performance Summary
This is a **demo report** generated without using AI credits. Your average score was {avg_score:.1f}/10.

### Strengths
- You completed the demo interview flow successfully
- The application is working correctly
- Ready for real interviews!

### Areas for Improvement
- This is placeholder feedback for testing
- Enable real AI mode for actual interview coaching

### 7-Day Practice Plan
**Day 1-2:** Review common interview questions
**Day 3-4:** Practice STAR method responses
**Day 5-6:** Mock interviews with peers
**Day 7:** Final preparation and rest

---
*This report was generated in Demo Mode. Disable Demo Mode for real AI feedback.*"""


def get_first_question(cv_text: str, jd_text: str, seniority: str, demo_mode: bool = False) -> Dict:
    """
    Generate the first interview question.
    
    Args:
        cv_text: Extracted text from CV/resume
        jd_text: Job description text
        seniority: Candidate seniority level
        demo_mode: If True, return mock response without API call
        
    Returns:
        Dict with greeting and first question
    """
    if demo_mode:
        return get_demo_first_question()
    
    client = get_openai_client()
    
    prompt = f"""Based on this candidate's CV and the job requirements, generate an opening greeting and the first interview question.

CANDIDATE'S CV:
{cv_text}

JOB DESCRIPTION:
{jd_text if jd_text else "General software engineering role"}

SENIORITY LEVEL: {seniority}

CRITICAL: The question must be SHORT and CONCISE — maximum 1-2 sentences. Do NOT ask multi-part questions or include sub-questions like (a), (b). Ask one simple, clear, focused question.

Respond with a JSON object:
{{
    "greeting": "<brief greeting, 1-2 sentences max>",
    "question": "<one short, focused interview question — max 2 sentences>"
}}"""

    # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
    # do not change this unless explicitly requested by the user
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional technical interviewer. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except json.JSONDecodeError:
        return {
            "greeting": "Welcome to your mock interview! I've reviewed your resume and I'm excited to learn more about your experience.",
            "question": "To start, could you tell me about a challenging project you've worked on recently and what made it challenging?"
        }


def evaluate_answer_and_get_next(
    cv_text: str,
    jd_text: str,
    seniority: str,
    conversation_history: List[Dict],
    current_answer: str,
    question_number: int,
    demo_mode: bool = False
) -> Dict:
    """
    Evaluate the candidate's answer and get the next question.
    
    Args:
        cv_text: Extracted text from CV/resume
        jd_text: Job description text
        seniority: Candidate seniority level
        conversation_history: List of previous messages
        current_answer: The candidate's current answer
        question_number: Current question number (1-5)
        demo_mode: If True, return mock response without API call
        
    Returns:
        Dict with score, justification, pro_tip, and next_question
    """
    if demo_mode:
        return get_demo_evaluation(question_number, current_answer)
    
    client = get_openai_client()
    
    system_prompt = build_system_prompt(cv_text, jd_text, seniority)
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({
        "role": "user",
        "content": f"My answer to question {question_number}: {current_answer}"
    })
    
    # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
    # do not change this unless explicitly requested by the user
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    response_text = response.choices[0].message.content
    
    try:
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            return result
    except json.JSONDecodeError:
        pass
    
    return {
        "score": 5,
        "justification": "Thank you for your answer.",
        "pro_tip": "Try to provide more specific examples from your experience.",
        "next_question": None if question_number >= TOTAL_QUESTIONS else "Can you tell me more about your experience?",
        "question_number": question_number
    }


def generate_final_report(
    cv_text: str,
    jd_text: str,
    seniority: str,
    questions: List[str],
    answers: List[str],
    scores: List[int],
    tips: List[str],
    demo_mode: bool = False
) -> str:
    """
    Generate a comprehensive final feedback report.
    
    Args:
        cv_text: Extracted text from CV/resume
        jd_text: Job description text
        seniority: Candidate seniority level
        questions: List of interview questions
        answers: List of candidate answers
        scores: List of scores for each answer
        tips: List of pro tips given
        demo_mode: If True, return mock report without API call
        
    Returns:
        Formatted feedback report string
    """
    if demo_mode:
        return get_demo_final_report(scores)
    
    client = get_openai_client()
    
    qa_summary = ""
    for i, (q, a, s, t) in enumerate(zip(questions, answers, scores, tips), 1):
        qa_summary += f"""
Question {i}: {q}
Answer: {a}
Score: {s}/10
Tip: {t}
---"""

    job_role = jd_text.split('\n')[0].strip() if jd_text else f"{seniority}-level role (based on CV)"

    prompt = f"""You are an expert interview coach. Write a SHORT, CONCISE feedback report that's easy to scan and act on. No fluff — every sentence must be useful.

CRITICAL: Keep the entire report under 500 words. Be punchy and direct. Use bullet points, not paragraphs.

Write the report in this EXACT structure:

# Your Interview Performance Report

## 1) Overall Analysis
- Performance: X/10
- Summary (2–3 sentences max — what went well and what didn't)

## 2) Performance Breakdown
Rate each (X/10, one line of evidence each):
- Answer Structure:
- Communication Clarity:
- Confidence & Delivery:
- Role Fit:
- Technical Depth:
- Problem Solving:
- Use of Examples:

## 3) What You Did Well
3 bullet points max. Each: strength + one quote/evidence from transcript.

## 4) What Needs Work
3 bullet points max. Each: weakness + evidence from transcript + one-line fix.

## 5) How a Stronger Answer Would Sound
Rewrite the weakest answer using STAR format. Keep it brief (4–5 sentences).

## 6) Your 7-Day Action Plan
One line per day:
- Day 1: [Focus] — [Exercise] (X min)
- Day 2–7: same format

## 7) Before Your Next Interview
3 bullet points: what to prepare, practice, and focus on.

Context:
Job Role: {job_role}
Job Description: {jd_text if jd_text else "Not provided"}
Resume: {cv_text[:1000]}

Interview Transcript:
{qa_summary}

AVERAGE PERFORMANCE: {sum(scores)/len(scores):.1f}/10

Remember: SHORT and ACTIONABLE. No generic advice. Cite the transcript."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a concise interview coach. Write short, specific, actionable feedback. Never be generic. Always cite the transcript. Keep the total report under 500 words."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=2000
    )
    
    return response.choices[0].message.content
