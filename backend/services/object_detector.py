"""
backend/services/object_detector.py
====================================
YOLO-based cheating object detection for SightFlow.

Place at: backend/services/object_detector.py

Detects: phone, laptop, tablet, book, earphone/headphone
Uses:    ultralytics YOLOv8 nano (auto-downloads ~6 MB on first run)

Install: pip install ultralytics
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── YOLO import (graceful fallback) ─────────────────────────────────────────
try:
    from ultralytics import YOLO as _YOLO
    _yolo_model = _YOLO("yolov8n.pt")   # downloads once (~6 MB) if not cached
    YOLO_AVAILABLE = True
    logger.info("YOLOv8 loaded successfully.")
except Exception as _e:
    _yolo_model = None
    YOLO_AVAILABLE = False
    logger.warning(f"YOLOv8 not available: {_e}. Object detection disabled.")


# ── COCO class names that count as cheating devices ─────────────────────────
# These are the exact strings YOLO/COCO uses.
CHEAT_CLASSES = {
    "cell phone":          "Phone",
    "laptop":              "Laptop",
    "tablet":              "Tablet",
    "book":                "Book",
    "remote":              "Remote/Device",
    "keyboard":            "External Keyboard",
    "mouse":               "Mouse",
    "headphones":          "Headphones",
    "earphone":            "Earphone",
}

# ── Confidence threshold ─────────────────────────────────────────────────────
# Raised to 0.55 (from 0.45) to reduce false positives on harmless objects.
CONFIDENCE_THRESHOLD = 0.55

# ── Per-object streak debounce ───────────────────────────────────────────────
# An object must appear in this many consecutive frames before being reported.
OBJECT_STREAK_REQUIRED: int = 3

# Internal streak counters keyed by friendly label (e.g. "Phone": 2)
_object_streaks: dict = {}


# ── Data class returned per detection ───────────────────────────────────────
@dataclass
class DetectedObject:
    label: str             # friendly name, e.g. "Phone"
    raw_class: str         # original YOLO class, e.g. "cell phone"
    confidence: float      # 0.0 – 1.0
    timestamp: float       # time.time() at detection
    bbox: List[int]        # [x1, y1, x2, y2] in pixels
    frame_index: int = 0   # frame number within session


# ── Main detection function ──────────────────────────────────────────────────
def detect_cheating_objects(
    frame: np.ndarray,
    frame_index: int = 0,
) -> List[DetectedObject]:
    """
    Run YOLO on one frame.  Returns list of DetectedObject for any
    cheating-related item confirmed across OBJECT_STREAK_REQUIRED consecutive
    frames.  Returns [] if YOLO not installed or nothing suspicious confirmed.

    Parameters
    ----------
    frame       : BGR numpy array (from OpenCV / decode_frame)
    frame_index : frame counter for logging in the report

    Changes vs original
    -------------------
    • CONFIDENCE_THRESHOLD raised 0.45 → 0.55 (fewer false hits)
    • Per-label streak counter: object must appear in 3 consecutive frames
      before being returned, eliminating single-frame phantom detections
    • Labels NOT seen this frame have their streak reset to 0
    """
    global _object_streaks

    if not YOLO_AVAILABLE or frame is None:
        return []

    # Track which labels are detected THIS frame
    seen_this_frame: dict[str, DetectedObject] = {}

    try:
        yolo_out = _yolo_model(frame, verbose=False)[0]

        for box in yolo_out.boxes:
            conf       = float(box.conf[0])
            class_id   = int(box.cls[0])
            class_name = _yolo_model.names[class_id].lower()

            if conf < CONFIDENCE_THRESHOLD:
                continue

            # Check if this class is in our cheating watchlist
            friendly = None
            for cheat_key, cheat_label in CHEAT_CLASSES.items():
                if cheat_key in class_name or class_name in cheat_key:
                    friendly = cheat_label
                    break

            if friendly is None:
                continue

            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]

            # Keep highest-confidence detection per label per frame
            if friendly not in seen_this_frame or conf > seen_this_frame[friendly].confidence:
                seen_this_frame[friendly] = DetectedObject(
                    label       = friendly,
                    raw_class   = class_name,
                    confidence  = round(conf, 3),
                    timestamp   = time.time(),
                    bbox        = [x1, y1, x2, y2],
                    frame_index = frame_index,
                )

    except Exception as e:
        logger.error(f"YOLO inference error: {e}")
        return []

    # ── Update streak counters ───────────────────────────────────────────────
    all_labels = set(CHEAT_CLASSES.values())
    confirmed  = []

    for label in all_labels:
        if label in seen_this_frame:
            _object_streaks[label] = _object_streaks.get(label, 0) + 1
        else:
            _object_streaks[label] = 0   # reset if not seen this frame

    # Only report labels that have been seen for enough consecutive frames
    for label, det in seen_this_frame.items():
        if _object_streaks.get(label, 0) >= OBJECT_STREAK_REQUIRED:
            confirmed.append(det)
            logger.info(
                f"Frame {frame_index}: confirmed '{label}' "
                f"(streak={_object_streaks[label]}, conf={det.confidence})"
            )

    return confirmed


def reset_object_streaks() -> None:
    """Call this when a new exam session starts to clear all streak counters."""
    global _object_streaks
    _object_streaks = {}


# ── Draw bounding boxes on frame (optional, for live monitor feed) ───────────
def draw_detections(frame: np.ndarray, detections: List[DetectedObject]) -> np.ndarray:
    """
    Draw YOLO bounding boxes on frame for live display.
    Optional – only needed if you want to show boxes in the webcam feed.

    Usage:
        annotated = draw_detections(frame, detections)
    """
    annotated = frame.copy()
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        label = f"{det.label} {det.confidence:.0%}"

        # Red box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # Label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), (0, 0, 255), -1)
        cv2.putText(
            annotated, label, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
        )

    return annotated