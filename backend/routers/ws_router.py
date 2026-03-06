"""
backend/routers/ws_router.py  —  FIXED VERSION
"""

import json
import time
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.models.session import SessionData, SessionEvent
from backend.services.session_store import get_session, update_session
from backend.services.vision import (
    decode_frame,
    get_face_embedding,
    compare_embeddings,
    detect_liveness,
    check_absence,
    analyze_frame_for_cheating,
)
from backend.services.risk_engine import calculate_risk_score

logger  = logging.getLogger(__name__)
router  = APIRouter()

LIVENESS_BUFFER = 5
_frame_buffers: dict = {}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")
    _frame_buffers[session_id] = []

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)

            # Accept both "type" and "action" so old + new JS both work
            msg_type = data.get("type") or data.get("action") or ""
            logger.info(f"[{session_id}] msg type='{msg_type}'")

            if msg_type == "register":
                response = await _handle_register(session_id, data)
                await websocket.send_text(json.dumps(response))

            elif msg_type == "frame":
                response = await _handle_frame(session_id, data)
                await websocket.send_text(json.dumps(response))

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                logger.warning(f"[{session_id}] Unknown msg type: '{msg_type}'")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        _frame_buffers.pop(session_id, None)
    except Exception as e:
        logger.error(f"WebSocket error [{session_id}]: {e}")
        _frame_buffers.pop(session_id, None)


async def _handle_register(session_id: str, data: dict) -> dict:
    session = get_session(session_id)
    if not session:
        return {"type": "register_result", "success": False,
                "message": "Session not found"}

    frame = decode_frame(data.get("frame", ""))
    if frame is None:
        return {"type": "register_result", "success": False,
                "message": "Could not decode frame — try again"}

    embedding = get_face_embedding(frame)
    if embedding is None:
        return {"type": "register_result", "success": False,
                "message": "No face detected — look directly at the camera"}

    session.registered_embedding = embedding
    update_session(session)
    logger.info(f"Face registered for {session_id}")
    return {"type": "register_result", "success": True,
            "message": "Face registered! Monitoring started."}


async def _handle_frame(session_id: str, data: dict) -> dict:
    session = get_session(session_id)
    if not session:
        return {"type": "error", "message": "Session not found"}

    b64 = data.get("frame", "")
    if not b64:
        return {"type": "error", "message": "No frame data"}

    frame = decode_frame(b64)
    if frame is None:
        return {"type": "error", "message": "Frame decode failed"}

    session.total_frames += 1

    # Face count + YOLO
    analysis   = analyze_frame_for_cheating(frame, frame_index=session.total_frames)
    face_count = analysis["face_count"]
    objects    = analysis["objects"]

    if objects:
        session.detected_objects.extend(objects)
        logger.info(f"[{session_id}] YOLO detected: {[o.label for o in objects]}")

    # Liveness
    buf = _frame_buffers.setdefault(session_id, [])
    buf.append(frame)
    if len(buf) > LIVENESS_BUFFER:
        buf.pop(0)

    is_live     = True
    live_reason = "Monitoring"
    if len(buf) >= 2:
        is_live, live_reason = detect_liveness(buf)

    # Identity
    identity_score = None
    identity_ok    = True
    if session.registered_embedding and face_count > 0:
        current_emb = get_face_embedding(frame)
        if current_emb:
            identity_score = compare_embeddings(session.registered_embedding, current_emb)
            session.identity_scores.append(identity_score)
            identity_ok = identity_score >= 0.45

    # Absence
    if face_count > 0:
        session.last_face_seen = time.time()
    is_absent = check_absence(session.last_face_seen, threshold_seconds=5)

    # Events
    event_type = "ok"
    if is_absent:
        session.absence_alerts += 1
        event_type = "absence"
        session.add_event(SessionEvent(event_type="absence", timestamp=time.time(),
                                       details="Candidate not visible", risk_points=20))
    elif face_count > 1:
        session.multi_face_alerts += 1
        event_type = "multi_face"
        session.add_event(SessionEvent(event_type="multi_face", timestamp=time.time(),
                                       details=f"{face_count} faces", risk_points=30))
    elif not is_live and len(buf) >= 2:
        session.liveness_fail_count += 1
        event_type = "liveness_fail"
        session.add_event(SessionEvent(event_type="liveness_fail", timestamp=time.time(),
                                       details=live_reason, risk_points=40))
    elif not identity_ok and identity_score is not None:
        session.face_mismatch_count += 1
        event_type = "face_mismatch"
        session.add_event(SessionEvent(event_type="face_mismatch", timestamp=time.time(),
                                       details=f"Score: {identity_score:.2f}", risk_points=50))

    for obj in objects:
        session.add_event(SessionEvent(event_type="object_detected", timestamp=obj.timestamp,
                                       details=f"{obj.label} ({obj.confidence:.0%})",
                                       risk_points=25))

    try:
        risk = calculate_risk_score(session)
    except Exception:
        risk = {"score": session.get_risk_score(), "level": session.get_risk_level()}

    update_session(session)

    objects_payload = [
        {"label": o.label, "raw_class": o.raw_class, "confidence": o.confidence,
         "timestamp": o.timestamp, "frame_index": o.frame_index, "bbox": o.bbox}
        for o in objects
    ]

    return {
        "type":           "frame_result",
        "face_count":     face_count,
        "event_type":     event_type,
        "is_live":        is_live,
        "identity_score": identity_score,
        "risk_score":     risk.get("score", 0),
        "risk_level":     risk.get("level", "Unknown"),
        "objects":        objects_payload,
        "frame_index":    session.total_frames,
    }