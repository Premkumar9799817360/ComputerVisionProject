"""
REST API routes for session management.
"""

import os
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.services.session_store import (
    create_session, get_session, end_session, list_sessions, delete_session
)
from backend.services.risk_engine import calculate_risk_score
from backend.services.llm_analysis import (
    generate_session_summary,
    generate_behavior_explanation,
    generate_compliance_recommendation,
)
from backend.services.report_generator import generate_pdf_report

router = APIRouter(prefix="/api/session", tags=["session"])


class CreateSessionRequest(BaseModel):
    candidate_name: str


@router.post("/create")
def create_new_session(req: CreateSessionRequest):
    session = create_session(req.candidate_name)
    return {
        "session_id": session.session_id,
        "candidate_name": session.candidate_name,
        "message": "Session created successfully",
    }


@router.get("/list")
def get_all_sessions():
    return {"sessions": list_sessions()}


@router.get("/{session_id}/status")
def get_session_status(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    risk = calculate_risk_score(session)
    return {
        "session": session.to_summary_dict(),
        "risk": risk,
    }


@router.post("/{session_id}/end")
def end_session_route(session_id: str):
    session = end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session ended", "session_id": session_id}


@router.get("/{session_id}/analysis")
def get_ai_analysis(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "summary": generate_session_summary(session),
        "explanation": generate_behavior_explanation(session),
        "recommendation": generate_compliance_recommendation(session),
        "risk": calculate_risk_score(session),
    }


@router.get("/{session_id}/report")
def download_report(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.end_time is None:
        session.end_time = time.time()

    report_path = generate_pdf_report(session)
    if not os.path.exists(report_path):
        raise HTTPException(status_code=500, detail="Report generation failed")

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"sightflow_report_{session_id}.pdf",
    )


@router.delete("/{session_id}")
def remove_session(session_id: str):
    delete_session(session_id)
    return {"message": "Session deleted"}