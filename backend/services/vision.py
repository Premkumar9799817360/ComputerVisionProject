"""
Face verification, liveness detection, multi-face detection, absence detection.
Uses OpenCV + face_recognition (open source, no paid APIs).
"""

import cv2
import numpy as np
import base64
import time
from typing import Optional, Tuple, List
import logging

from backend.services.object_detector import (
    detect_cheating_objects,
    draw_detections,
    YOLO_AVAILABLE,
    DetectedObject,
)

logger = logging.getLogger(__name__)

# ── Face recognition (optional, falls back to OpenCV) ───────────────────────
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except Exception:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("face_recognition not available; using OpenCV fallback.")

# ── OpenCV cascade detectors (always available) ──────────────────────────────
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
_eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml"
)

logger.info(
    f"Vision module loaded. "
    f"face_recognition={FACE_RECOGNITION_AVAILABLE}, YOLO={YOLO_AVAILABLE}"
)

# ── Multi-face debounce state (per-session streak counter) ───────────────────
# Use a dict keyed by session_id if you have multiple sessions.
# For single-session use, a module-level counter is fine.
_multi_face_streak: int = 0
MULTI_FACE_STREAK_REQUIRED: int = 3   # consecutive frames before alerting


# ============================================================================
# Frame decode
# ============================================================================

def decode_frame(b64_data: str) -> Optional[np.ndarray]:
    """Decode base64 image string to BGR numpy array."""
    try:
        if "," in b64_data:
            b64_data = b64_data.split(",")[1]
        img_bytes = base64.b64decode(b64_data)
        arr       = np.frombuffer(img_bytes, dtype=np.uint8)
        frame     = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        logger.error(f"Frame decode error: {e}")
        return None


# ============================================================================
# Face utilities
# ============================================================================

def _nms_faces(faces) -> List:
    """
    Non-maximum suppression: remove overlapping Haar detections.
    Keeps the largest box when two boxes overlap more than 30%.
    """
    if len(faces) == 0:
        return []

    # Convert (x, y, w, h) → (x1, y1, x2, y2)
    boxes = [(x, y, x + w, y + h) for (x, y, w, h) in faces]

    # Sort by area descending so we keep bigger (more reliable) boxes first
    boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)

    keep = []
    for b1 in boxes:
        suppressed = False
        for b2 in keep:
            ix1 = max(b1[0], b2[0])
            iy1 = max(b1[1], b2[1])
            ix2 = min(b1[2], b2[2])
            iy2 = min(b1[3], b2[3])
            if ix2 > ix1 and iy2 > iy1:
                inter = (ix2 - ix1) * (iy2 - iy1)
                area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
                iou   = inter / area1
                if iou > 0.30:   # >30 % overlap → suppress smaller box
                    suppressed = True
                    break
        if not suppressed:
            keep.append(b1)

    # Convert back to (x, y, w, h)
    return [(x1, y1, x2 - x1, y2 - y1) for (x1, y1, x2, y2) in keep]


def detect_faces_opencv(frame: np.ndarray) -> List:
    """
    Detect faces using OpenCV Haar cascade.
    Returns list of (x, y, w, h).

    Changes vs original:
      • equalizeHist  → better contrast under variable lighting
      • minNeighbors=8 (was 5) → far fewer false positives
      • minSize=(80,80) (was 60,60) → ignores sub-face regions
      • NMS pass → merges any remaining overlapping boxes
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)          # improve contrast

    faces = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=8,    # ← raised from 5; reduces false detections
        minSize=(80, 80),  # ← raised from 60; ignores eye/mouth sub-regions
    )

    if len(faces) == 0:
        return []

    return _nms_faces(faces)


def get_face_embedding(frame: np.ndarray) -> Optional[list]:
    """Extract face embedding. Returns list of floats, or None if no face."""
    if FACE_RECOGNITION_AVAILABLE:
        rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if encodings:
            return encodings[0].tolist()

    # Fallback: histogram of face region
    faces = detect_faces_opencv(frame)
    if len(faces) > 0:
        x, y, w, h = faces[0]
        face_roi   = cv2.resize(frame[y:y+h, x:x+w], (64, 64))
        gray       = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        hist       = cv2.calcHist([gray], [0], None, [128], [0, 256])
        cv2.normalize(hist, hist)
        return hist.flatten().tolist()
    return None


def compare_embeddings(emb1: list, emb2: list) -> float:
    """Compare two embeddings. Returns similarity score 0.0–1.0."""
    if FACE_RECOGNITION_AVAILABLE:
        a        = np.array(emb1)
        b        = np.array(emb2)
        distance = np.linalg.norm(a - b)
        return round(float(max(0.0, 1.0 - distance / 0.6)), 3)

    # Cosine similarity for histogram fallback
    a      = np.array(emb1)
    b      = np.array(emb2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return round(float(np.dot(a, b) / (norm_a * norm_b)), 3)


def count_faces(frame: np.ndarray) -> int:
    """
    Count number of faces visible in frame.
    Caps result at 4 — anything higher is almost always a cascade error.
    """
    if FACE_RECOGNITION_AVAILABLE:
        rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="hog")
        return len(locations)

    raw_count = len(detect_faces_opencv(frame))
    return min(raw_count, 4)   # sanity cap


def detect_liveness(frames: List[np.ndarray]) -> Tuple[bool, str]:
    """
    Simple liveness check: eye presence + inter-frame motion.
    Returns (is_live: bool, reason: str).
    """
    if len(frames) < 2:
        return True, "Not enough frames"

    # Eye presence check in last 3 frames
    eyes_found = False
    for frame in frames[-3:]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        eyes = _eye_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
        )
        if len(eyes) >= 1:
            eyes_found = True
            break

    # Frame-to-frame motion check
    diffs = []
    for i in range(1, min(len(frames), 5)):
        f1 = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY).astype(float)
        f2 = cv2.cvtColor(frames[i],     cv2.COLOR_BGR2GRAY).astype(float)
        diffs.append(np.mean(np.abs(f1 - f2)))

    avg_diff = float(np.mean(diffs)) if diffs else 0.0

    if avg_diff < 0.5 and not eyes_found:
        return False, f"Static image detected (diff={avg_diff:.2f}, no eyes)"
    if avg_diff < 0.3:
        return False, f"No movement detected (diff={avg_diff:.2f})"

    return True, f"Live (motion={avg_diff:.2f}, eyes={eyes_found})"


def check_absence(last_face_time: float, threshold_seconds: int = 5) -> bool:
    """Return True if no face has been seen for longer than threshold."""
    return (time.time() - last_face_time) > threshold_seconds


# ============================================================================
# Unified frame analysis  ← THIS is what ws_router must call
# ============================================================================

def analyze_frame_for_cheating(
    frame: np.ndarray,
    frame_index: int = 0,
    draw_boxes: bool = False,
) -> dict:
    """
    Run face count + YOLO object detection on one decoded frame.

    Returns
    -------
    dict with keys:
        "face_count"        : int  – raw face count this frame
        "multi_face_alert"  : bool – True only after MULTI_FACE_STREAK_REQUIRED
                                     consecutive frames with >1 face (debounced)
        "objects"           : List[DetectedObject] – cheating objects YOLO found
        "annotated"         : np.ndarray | None    – frame with boxes (if draw_boxes)

    How to use in ws_router.py
    ---------------------------
        frame  = decode_frame(b64_data)
        result = analyze_frame_for_cheating(frame, frame_index=session.total_frames)

        if result["multi_face_alert"]:
            session.add_event("Multiple Faces")   # fires only after 3 consecutive frames

        if result["objects"]:
            session.detected_objects.extend(result["objects"])
    """
    global _multi_face_streak

    if frame is None:
        return {
            "face_count": 0,
            "multi_face_alert": False,
            "objects": [],
            "annotated": None,
        }

    face_count = count_faces(frame)
    objects    = detect_cheating_objects(frame, frame_index=frame_index)

    # ── Debounced multi-face alert ───────────────────────────────────────────
    if face_count > 1:
        _multi_face_streak += 1
    else:
        _multi_face_streak = 0   # reset on any clean frame

    multi_face_alert = (_multi_face_streak >= MULTI_FACE_STREAK_REQUIRED)

    # Only log / annotate when something suspicious is confirmed
    annotated = None
    if draw_boxes and objects:
        annotated = draw_detections(frame, objects)

    if objects or multi_face_alert:
        logger.info(
            f"Frame {frame_index}: {face_count} face(s) "
            f"(streak={_multi_face_streak}), "
            f"alert={multi_face_alert}, "
            f"objects={[o.label for o in objects]}"
        )

    return {
        "face_count":       face_count,
        "multi_face_alert": multi_face_alert,
        "objects":          objects,
        "annotated":        annotated,
    }


def reset_multi_face_streak() -> None:
    """Call this when a new exam session starts to clear the streak counter."""
    global _multi_face_streak
    _multi_face_streak = 0