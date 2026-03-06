from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import time


@dataclass
class SessionEvent:
    event_type: str        # "face_mismatch", "liveness_fail", "multi_face", "absence", "ok"
    timestamp: float
    details: str
    risk_points: int = 0

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "time_str": datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S"),
            "details": self.details,
            "risk_points": self.risk_points,
        }


@dataclass
class SessionData:
    session_id: str
    candidate_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    events: List[SessionEvent] = field(default_factory=list)
    registered_embedding: Optional[list] = None
    total_frames: int = 0
    last_face_seen: float = field(default_factory=time.time)
    absence_alerts: int = 0
    multi_face_alerts: int = 0
    liveness_fail_count: int = 0
    face_mismatch_count: int = 0
    identity_scores: List[float] = field(default_factory=list)
    detected_objects: list = field(default_factory=list)

    def add_event(self, event: SessionEvent):
        self.events.append(event)

    def get_risk_score(self) -> int:
        score = 0
        score += self.face_mismatch_count * 50
        score += self.liveness_fail_count * 40
        score += self.multi_face_alerts * 30
        score += self.absence_alerts * 20
        return min(score, 100)

    def get_risk_level(self) -> str:
        score = self.get_risk_score()
        if score >= 60:
            return "HIGH RISK"
        elif score >= 30:
            return "WARNING"
        return "SAFE"

    def get_avg_identity_score(self) -> float:
        if not self.identity_scores:
            return 0.0
        return round(sum(self.identity_scores) / len(self.identity_scores), 2)

    def to_summary_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "candidate_name": self.candidate_name,
            "start_time": datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.fromtimestamp(self.end_time).strftime("%Y-%m-%d %H:%M:%S") if self.end_time else "Active",
            "duration_seconds": int((self.end_time or time.time()) - self.start_time),
            "total_frames": self.total_frames,
            "risk_score": self.get_risk_score(),
            "risk_level": self.get_risk_level(),
            "face_mismatch_count": self.face_mismatch_count,
            "liveness_fail_count": self.liveness_fail_count,
            "multi_face_alerts": self.multi_face_alerts,
            "absence_alerts": self.absence_alerts,
            "avg_identity_score": self.get_avg_identity_score(),
            "events": [e.to_dict() for e in self.events[-20:]],  # last 20 events
        }