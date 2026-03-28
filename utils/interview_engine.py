"""
Interview engine for managing AI-powered mock interviews.
Handles OpenAI API calls, prompt building, and interview logic.
Supports both standard OpenAI API keys and Replit AI Integrations.
"""

import json
import os
from typing import Dict, List

from openai import OpenAI

from config import OPENAI_MODEL, TOTAL_QUESTIONS


def get_openai_client() -> OpenAI:
    """
    Create an OpenAI client.

    Priority:
    1. Standard OpenAI environment variables for local/dev use
    2. Replit AI Integration environment variables
    """
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        return OpenAI(
            api_key=openai_api_key,
            timeout=30.0,
            max_retries=1,
        )

    replit_api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    replit_base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

    if replit_api_key and replit_base_url:
        return OpenAI(
            api_key=replit_api_key,
            base_url=replit_base_url,
            timeout=30.0,
            max_retries=1,
        )

    raise RuntimeError(
        "No API credentials found. Set OPENAI_API_KEY or "
        "AI_INTEGRATIONS_OPENAI_API_KEY / AI_INTEGRATIONS_OPENAI_BASE_URL."
    )


def is_quick_start(cv_text: str) -> bool:
    return cv_text.startswith("Role: ") and len(cv_text) < 100


def get_role_text(cv_text: str, jd_text: str, seniority: str) -> str:
    if is_quick_start(cv_text):
        return cv_text.replace("Role: ", "").strip()

    if jd_text and jd_text.strip():
        first_line = jd_text.strip().splitlines()[0].strip()
        if first_line:
            return first_line

    return f"{seniority}-level role"


def build_system_prompt(cv_text: str, jd_text: str, seniority: str) -> str:
    quick_mode = is_quick_start(cv_text)

    if quick_mode:
        role = cv_text.replace("Role: ", "").strip()
        context_block = f"""TARGET ROLE: {role}
SENIORITY LEVEL: {seniority}

NOTE: No CV was provided. Ask interview questions appropriate for a {seniority}-level {role} position.
Questions must be relevant to the role, realistic, and concise."""
    else:
        context_block = f"""CANDIDATE'S CV/RESUME:
{cv_text}

JOB DESCRIPTION/REQUIREMENTS:
{jd_text if jd_text else "General role based on the candidate's background."}"""

    return f"""You are an expert interview coach and mock interviewer conducting an interview for a {seniority}-level position.

{context_block}

RULES:
- Ask exactly {TOTAL_QUESTIONS} questions in total.
- Ask only ONE question at a time.
- Keep each question SHORT and CONCISE.
- After evaluating the answer, respond ONLY with valid JSON.
- Be encouraging but honest.
- Score from 0 to 10.
- Give a short justification.
- Give a short, practical pro tip.
- Keep the next question relevant to the user's role and previous context.
- If this was the final question, set next_question to null.

STRICT JSON FORMAT:
{{
  "score": <0-10>,
  "justification": "<one short sentence>",
  "pro_tip": "<one short actionable tip>",
  "next_question": "<next role-relevant question or null>",
  "question_number": <number>
}}"""


def safe_json_loads(text: str) -> Dict:
    """
    Try to parse a JSON object even if there is extra text around it.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(text[start_idx:end_idx + 1])
        except Exception:
            pass

    raise ValueError("Could not parse JSON from model response.")


def get_demo_first_question() -> Dict:
    return {
        "greeting": "Welcome to your demo interview! This is a test mode that doesn't use AI credits.",
        "question": "Tell me about a recent project you worked on and what your role was in it.",
    }


def get_demo_evaluation(question_number: int, answer: str) -> Dict:
    demo_scores = [7, 8, 7, 8, 7]
    demo_tips = [
        "Try to quantify your achievements with specific numbers or metrics.",
        "Use the STAR method to make your answer more structured.",
        "Mention one concrete example to support your answer.",
        "Focus on your actions and the result you achieved.",
        "Keep your answer concise and role-relevant.",
    ]

    idx = min(question_number - 1, len(demo_scores) - 1)

    next_question = None
    if question_number < TOTAL_QUESTIONS:
        next_question = f"Can you describe another example that shows your suitability for this role?"

    return {
        "score": demo_scores[idx],
        "justification": "Good answer with relevant context. This is a demo evaluation.",
        "pro_tip": demo_tips[idx],
        "next_question": next_question,
        "question_number": question_number,
    }


def get_demo_final_report(scores: List[int]) -> str:
    avg_score = sum(scores) / len(scores) if scores else 5
    return f"""## Interview Feedback Report (Demo Mode)

### Performance Summary
This is a demo report. Your average score was {avg_score:.1f}/10.

### Strengths
- You completed the demo interview flow successfully
- The app is functioning end-to-end
- You are ready to practice with real AI evaluation

### Areas for Improvement
- Use more specific examples
- Structure answers more clearly
- Quantify your impact where possible

### 7-Day Practice Plan
- Day 1: Practice intro answers
- Day 2: Practice STAR method
- Day 3: Record and review answers
- Day 4: Improve clarity and examples
- Day 5: Practice role-specific questions
- Day 6: Do a full mock interview
- Day 7: Review and refine

---
*This report was generated in Demo Mode.*"""


def fallback_first_question(cv_text: str, jd_text: str, seniority: str) -> Dict:
    role = get_role_text(cv_text, jd_text, seniority)
    return {
        "greeting": f"Hello, thank you for interviewing for the {seniority}-level {role} position.",
        "question": f"What experience do you have that makes you a strong fit for the {role} role?",
    }


def fallback_next_question(cv_text: str, jd_text: str, seniority: str, question_number: int) -> str | None:
    if question_number >= TOTAL_QUESTIONS:
        return None

    role = get_role_text(cv_text, jd_text, seniority)

    fallback_questions = [
        f"Can you describe a real example where you solved a problem relevant to the {role} role?",
        f"How do you prioritize tasks and responsibilities in a {role} position?",
        f"What tools, processes, or methods have you used that are relevant to the {role} role?",
        f"Tell me about a challenge you faced in a similar role and how you handled it.",
        f"Why do you believe you are well suited for this {role} opportunity?",
    ]

    idx = min(max(question_number - 1, 0), len(fallback_questions) - 1)
    return fallback_questions[idx]


def get_first_question(cv_text: str, jd_text: str, seniority: str, demo_mode: bool = False) -> Dict:
    if demo_mode:
        return get_demo_first_question()

    try:
        client = get_openai_client()

        quick_mode = is_quick_start(cv_text)

        if quick_mode:
            role = cv_text.replace("Role: ", "").strip()
            context = f"""The candidate is interviewing for a {seniority}-level {role} position.
No CV was provided.
Generate a brief greeting and one concise role-relevant first interview question."""
        else:
            context = f"""Based on this candidate's CV and job requirements, generate:
1. a short greeting
2. one concise first interview question

CANDIDATE CV:
{cv_text}

JOB DESCRIPTION:
{jd_text if jd_text else "General role based on candidate background"}"""

        prompt = f"""{context}

Respond ONLY with valid JSON:
{{
  "greeting": "<brief greeting>",
  "question": "<one concise role-relevant interview question>"
}}"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional interviewer. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        result = safe_json_loads(response.choices[0].message.content)

        greeting = result.get("greeting", "").strip()
        question = result.get("question", "").strip()

        if not greeting or not question:
            return fallback_first_question(cv_text, jd_text, seniority)

        return {
            "greeting": greeting,
            "question": question,
        }

    except Exception:
        return fallback_first_question(cv_text, jd_text, seniority)


def evaluate_answer_and_get_next(
    cv_text: str,
    jd_text: str,
    seniority: str,
    conversation_history: List[Dict],
    current_answer: str,
    question_number: int,
    demo_mode: bool = False,
) -> Dict:
    if demo_mode:
        return get_demo_evaluation(question_number, current_answer)

    try:
        client = get_openai_client()
        system_prompt = build_system_prompt(cv_text, jd_text, seniority)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({
            "role": "user",
            "content": f"My answer to question {question_number}: {current_answer}",
        })

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content
        result = safe_json_loads(response_text)

        score = result.get("score", 5)
        justification = result.get("justification", "Your answer addressed the question.")
        pro_tip = result.get("pro_tip", "Use a more structured example and clearer steps.")
        next_question = result.get("next_question")

        try:
            score = int(score)
        except Exception:
            score = 5

        if score < 0:
            score = 0
        if score > 10:
            score = 10

        if question_number >= TOTAL_QUESTIONS:
            next_question = None
        elif not next_question:
            next_question = fallback_next_question(cv_text, jd_text, seniority, question_number)

        return {
            "score": score,
            "justification": str(justification),
            "pro_tip": str(pro_tip),
            "next_question": next_question,
            "question_number": question_number,
        }

    except Exception as e:
        raise RuntimeError(f"OpenAI evaluation failed: {str(e)}")


def generate_final_report(
    cv_text: str,
    jd_text: str,
    seniority: str,
    questions: List[str],
    answers: List[str],
    scores: List[int],
    tips: List[str],
    demo_mode: bool = False,
) -> str:
    if demo_mode:
        return get_demo_final_report(scores)

    try:
        client = get_openai_client()

        qa_summary = ""
        for i, (q, a, s, t) in enumerate(zip(questions, answers, scores, tips), 1):
            qa_summary += f"""
Question {i}: {q}
Answer: {a}
Score: {s}/10
Tip: {t}
---"""

        job_role = get_role_text(cv_text, jd_text, seniority)
        avg_score = sum(scores) / len(scores) if scores else 0

        prompt = f"""You are an expert interview coach.

Write a SHORT, clear, useful interview report in markdown.

Use this structure:

# Your Interview Performance Report

## 1) Overall Analysis
- Performance: X/10
- Summary: 2-3 short sentences

## 2) What You Did Well
- 3 bullet points max

## 3) What Needs Work
- 3 bullet points max

## 4) Stronger Answer Example
- Rewrite one weak answer in a stronger way using STAR format

## 5) 7-Day Practice Plan
- Create a practical 7-day improvement plan based on the candidate's weak areas from the interview
- Each day must include:
  - the focus area
  - one specific exercise
  - a recommended practice duration in minutes
- Use realistic durations such as 20 min, 30 min, 45 min, or 60 min depending on how much improvement is needed
- If the candidate performed weakly in an area, assign more time
- If the candidate performed reasonably well, assign less time
- Format exactly like:
  - Day 1: [Focus] — [Exercise] ([X min])
  - Day 2: [Focus] — [Exercise] ([X min])
  - Day 3: [Focus] — [Exercise] ([X min])
  - Day 4: [Focus] — [Exercise] ([X min])
  - Day 5: [Focus] — [Exercise] ([X min])
  - Day 6: [Focus] — [Exercise] ([X min])
  - Day 7: [Focus] — [Exercise] ([X min])

## 6) Before Your Next Interview
- 3 bullet points

Context:
Role: {job_role}
Seniority: {seniority}
Job Description: {jd_text if jd_text else "Not provided"}

Transcript:
{qa_summary}

Average score: {avg_score:.1f}/10

Keep it practical, concise, and role-relevant."""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a concise interview coach. Be practical, clear, and brief."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1800,
        )

        text = response.choices[0].message.content
        if text and text.strip():
            return text

        raise ValueError("Empty final report response.")

    except Exception as e:
        avg_score = sum(scores) / len(scores) if scores else 0
        role = get_role_text(cv_text, jd_text, seniority)

        return f"""# Your Interview Performance Report

## 1) Overall Analysis
- Performance: {avg_score:.1f}/10
- Summary: You completed the interview for the {role} role, but full AI report generation was unavailable.

## 2) What You Did Well
- You completed the interview flow successfully
- You attempted role-relevant responses
- You now have a baseline to improve from

## 3) What Needs Work
- Use more specific examples
- Structure answers more clearly
- Explain your actions and outcomes more directly

## 4) Stronger Answer Example
Use STAR:
- Situation: Brief context
- Task: What needed to be done
- Action: What you specifically did
- Result: What outcome you achieved

## 5) 7-Day Practice Plan
- Day 1: Review the questions you were asked
- Day 2: Rewrite weak answers using STAR
- Day 3: Practice speaking answers aloud
- Day 4: Add role-specific examples
- Day 5: Improve clarity and confidence
- Day 6: Do another mock interview
- Day 7: Review progress and refine

## 6) Before Your Next Interview
- Prepare 3 strong examples from your experience
- Practice concise, structured answers
- Focus on role-relevant achievements

---
AI report generation fallback used due to: {str(e)}
"""