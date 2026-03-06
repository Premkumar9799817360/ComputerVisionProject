"""
LLM-powered session analysis using Groq API (free tier).
Generates: session summary, behavior explanation, compliance report text.
"""

import json
import logging
from backend.config import GROQ_API_KEY
from backend.models.session import SessionData
from backend.services.risk_engine import calculate_risk_score
from groq import Groq
logger = logging.getLogger(__name__)

print("GROQ_API_KEY in llm_analysis.py:", GROQ_API_KEY)  # Debug print to verify the API key is loaded
def test_groq():
    try:
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",   # Simple stable model
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ]
        )

        print("✅ API WORKING")
        print(response)
        print("Response:", response.choices[0].message.content)

    except Exception as e:
        print("❌ ERROR:", str(e))
test_groq()
def _call_groq(prompt: str, system: str = "You are an AI proctoring analyst.") -> str:
    """Call Groq LLM API (free). Falls back to rule-based output if no key."""
    if not GROQ_API_KEY or GROQ_API_KEY == "gsk_ey1gxpRZn8xSq8NkU14BWGdyb3FYy2O5vo9HAiDgNQDrHZAz2dq5d":
        return _rule_based_fallback(prompt)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return _rule_based_fallback(prompt)


def _rule_based_fallback(prompt: str) -> str:
    """Rule-based fallback when no API key is set."""
    if "summary" in prompt.lower():
        return "Session analysis complete. Please configure GROQ_API_KEY in .env for AI-generated summaries. The session data has been recorded and risk scoring is available above."
    if "explanation" in prompt.lower():
        return "Risk explanation unavailable without GROQ_API_KEY. Please review the event log and risk breakdown for details."
    return "AI analysis requires GROQ_API_KEY. Please add your free Groq API key to the .env file."


def generate_session_summary(session: SessionData) -> str:
    """Generate natural language session summary."""
    risk = calculate_risk_score(session)
    summary_data = session.to_summary_dict()

    prompt = f"""
You are an AI proctoring analyst. Generate a professional session summary report.

Session Data:
- Candidate: {session.candidate_name}
- Duration: {summary_data['duration_seconds']} seconds
- Total frames analyzed: {session.total_frames}
- Risk Score: {risk['score']}/100 ({risk['level']})
- Identity match average: {session.get_avg_identity_score()*100:.1f}%
- Face mismatch incidents: {session.face_mismatch_count}
- Liveness failures: {session.liveness_fail_count}
- Multiple face detections: {session.multi_face_alerts}
- Absence events: {session.absence_alerts}

Write a 3-4 sentence professional summary explaining what happened during the session. Be factual and concise.
"""
    return _call_groq(prompt)


def generate_behavior_explanation(session: SessionData) -> str:
    """Generate explainable AI reasoning for risk score."""
    risk = calculate_risk_score(session)

    prompt = f"""
You are an Explainable AI system for proctoring. Explain WHY the risk score is {risk['score']}/100.

Risk Breakdown:
- Face mismatch incidents: {session.face_mismatch_count} (contributes {risk['breakdown']['face_mismatch']} points)
- Liveness detection failures: {session.liveness_fail_count} (contributes {risk['breakdown']['liveness_fail']} points)
- Multiple faces detected: {session.multi_face_alerts} times (contributes {risk['breakdown']['multi_face']} points)
- Candidate absence events: {session.absence_alerts} times (contributes {risk['breakdown']['absence']} points)

Explain the reasoning in 2-3 sentences. Be specific about which factors contributed most.
"""
    return _call_groq(prompt)


def generate_compliance_recommendation(session: SessionData) -> str:
    """Generate compliance recommendation."""
    risk = calculate_risk_score(session)

    prompt = f"""
You are a compliance officer AI. Based on this proctoring session:
- Risk Level: {risk['level']} (score: {risk['score']}/100)
- Identity confidence: {session.get_avg_identity_score()*100:.1f}%
- Suspicious events: {len(session.events)} total

Provide a 2-3 sentence compliance recommendation for the HR team or exam administrator. Be direct and actionable.
"""
    return _call_groq(prompt, system="You are a compliance officer AI assistant.")