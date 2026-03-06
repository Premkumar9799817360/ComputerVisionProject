"""
Risk scoring engine for SightFlow.
Calculates risk score from session events.
"""

from backend.models.session import SessionData


RISK_WEIGHTS = {
    "face_mismatch": 50,
    "liveness_fail": 40,
    "multi_face": 30,
    "absence": 20,
}


def calculate_risk_score(session: SessionData) -> dict:
    score = 0
    breakdown = {}

    fm = session.face_mismatch_count
    lf = session.liveness_fail_count
    mf = session.multi_face_alerts
    ab = session.absence_alerts

    breakdown["face_mismatch"] = fm * RISK_WEIGHTS["face_mismatch"]
    breakdown["liveness_fail"] = lf * RISK_WEIGHTS["liveness_fail"]
    breakdown["multi_face"] = mf * RISK_WEIGHTS["multi_face"]
    breakdown["absence"] = ab * RISK_WEIGHTS["absence"]

    score = sum(breakdown.values())
    score = min(score, 100)

    if score >= 60:
        level = "HIGH RISK"
        color = "danger"
        recommendation = "Manual review strongly recommended before any certification or approval."
    elif score >= 30:
        level = "WARNING"
        color = "warning"
        recommendation = "Review session events carefully. Consider follow-up verification."
    else:
        level = "SAFE"
        color = "success"
        recommendation = "Session appears clean. No immediate action required."

    return {
        "score": score,
        "level": level,
        "color": color,
        "breakdown": breakdown,
        "recommendation": recommendation,
        "counts": {
            "face_mismatch": fm,
            "liveness_fail": lf,
            "multi_face": mf,
            "absence": ab,
        }
    }