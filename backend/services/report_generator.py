# """
# PDF Report Generator for SightFlow sessions.
# Stylish Production Version - uses only fpdf2 + matplotlib (no new dependencies)
# """

# import os
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# import matplotlib.gridspec as gridspec
# import numpy as np
# from fpdf import FPDF
# from datetime import datetime

# from backend.models.session import SessionData
# from backend.services.risk_engine import calculate_risk_score

# # Optional LLM imports (safe)
# try:
#     from backend.services.llm_analysis import (
#         generate_session_summary,
#         generate_behavior_explanation,
#         generate_compliance_recommendation,
#     )
#     LLM_AVAILABLE = True
# except Exception:
#     LLM_AVAILABLE = False


# # ==============================
# # Reports Folder
# # ==============================
# REPORTS_DIR = "reports"
# os.makedirs(REPORTS_DIR, exist_ok=True)


# # ==============================
# # Design Tokens
# # ==============================
# COLOR_BG        = (15,  23,  42)   # dark navy
# COLOR_CARD      = (30,  41,  59)   # slate card
# COLOR_ACCENT    = (99,  102, 241)  # indigo
# COLOR_GREEN     = (34,  197, 94)
# COLOR_YELLOW    = (234, 179, 8)
# COLOR_RED       = (239, 68,  68)
# COLOR_WHITE     = (255, 255, 255)
# COLOR_MUTED     = (148, 163, 184)
# COLOR_BORDER    = (51,  65,  85)

# RISK_COLORS = {
#     "Low":      COLOR_GREEN,
#     "Moderate": COLOR_YELLOW,
#     "High":     COLOR_RED,
#     "Critical": (220, 38,  38),
#     "Unknown":  COLOR_MUTED,
# }

# def _hex(rgb):
#     return "#{:02X}{:02X}{:02X}".format(*rgb)

# def _mpl(rgb):
#     return tuple(c / 255 for c in rgb)


# # ==============================
# # Text Sanitiser
# # ==============================

# def clean_text_for_pdf(text: str) -> str:
#     if not text:
#         return ""
#     replacements = {
#         "\u2013": "-", "\u2014": "-",
#         "\u201C": '"', "\u201D": '"',
#         "\u2018": "'", "\u2019": "'",
#         "\u2022": "-", "\u00A0": " ", "\u202F": " ",
#     }
#     for k, v in replacements.items():
#         text = text.replace(k, v)
#     return text.encode("latin-1", "ignore").decode("latin-1")


# # ==============================
# # Chart Helpers
# # ==============================

# def _risk_level_color(level: str):
#     return _mpl(RISK_COLORS.get(level, COLOR_MUTED))


# def _generate_risk_chart(session: SessionData, path: str):
#     """Stylish horizontal bar chart with gradient-style colouring."""
#     try:
#         risk = calculate_risk_score(session)
#         bd   = risk.get("breakdown", {})

#         labels = ["Face Mismatch", "Liveness Fail", "Multi Face", "Absence"]
#         keys   = ["face_mismatch",  "liveness_fail",  "multi_face", "absence"]
#         values = [bd.get(k, 0) for k in keys]
#         bar_colors = [_mpl(COLOR_ACCENT), _mpl(COLOR_RED),
#                       _mpl(COLOR_YELLOW), _mpl(COLOR_GREEN)]

#         fig, ax = plt.subplots(figsize=(8, 3.2))
#         fig.patch.set_facecolor(_mpl(COLOR_CARD))
#         ax.set_facecolor(_mpl(COLOR_CARD))

#         y_pos = np.arange(len(labels))
#         bars  = ax.barh(y_pos, values, height=0.55,
#                         color=bar_colors, edgecolor="none",
#                         zorder=3)

#         # Gridlines
#         ax.xaxis.grid(True, color=_mpl(COLOR_BORDER), linewidth=0.6, zorder=0)
#         ax.set_axisbelow(True)

#         # Value labels
#         for bar, val in zip(bars, values):
#             if val > 0:
#                 ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
#                         str(val), va="center", ha="left",
#                         color=_mpl(COLOR_WHITE), fontsize=9, fontweight="bold")

#         ax.set_yticks(y_pos)
#         ax.set_yticklabels(labels, color=_mpl(COLOR_WHITE), fontsize=10)
#         ax.tick_params(axis="x", colors=_mpl(COLOR_MUTED), labelsize=8)
#         ax.set_xlim(0, max(max(values) + 15, 60))

#         for spine in ax.spines.values():
#             spine.set_visible(False)

#         ax.set_title("Risk Score Breakdown", color=_mpl(COLOR_WHITE),
#                      fontsize=12, fontweight="bold", pad=10)

#         plt.tight_layout(pad=0.8)
#         plt.savefig(path, dpi=140, facecolor=fig.get_facecolor())
#         plt.close()
#     except Exception:
#         pass


# def _generate_gauge_chart(score: int, level: str, path: str):
#     """Semi-circle gauge for overall risk score."""
#     try:
#         fig, ax = plt.subplots(figsize=(4.5, 2.8), subplot_kw={"projection": "polar"})
#         fig.patch.set_facecolor(_mpl(COLOR_CARD))
#         ax.set_facecolor(_mpl(COLOR_CARD))

#         # Draw background arc
#         theta_bg = np.linspace(np.pi, 0, 200)
#         ax.plot(theta_bg, [1] * 200, linewidth=18,
#                 color=_mpl(COLOR_BORDER), solid_capstyle="round")

#         # Draw score arc
#         fill_angle = np.pi * (1 - score / 100)
#         theta_fg   = np.linspace(np.pi, fill_angle, 200)
#         arc_color  = _mpl(RISK_COLORS.get(level, COLOR_MUTED))
#         ax.plot(theta_fg, [1] * 200, linewidth=18,
#                 color=arc_color, solid_capstyle="round")

#         # Score text
#         ax.text(0, 0, f"{score}", ha="center", va="center",
#                 fontsize=28, fontweight="bold",
#                 color=_mpl(COLOR_WHITE), transform=ax.transData)
#         ax.text(0, -0.35, level.upper(), ha="center", va="center",
#                 fontsize=10, color=arc_color, fontweight="bold",
#                 transform=ax.transData)

#         ax.set_ylim(0, 1.3)
#         ax.set_xlim(0, np.pi)
#         ax.axis("off")
#         ax.set_thetamin(0)
#         ax.set_thetamax(180)

#         plt.tight_layout(pad=0.2)
#         plt.savefig(path, dpi=140, facecolor=fig.get_facecolor(),
#                     bbox_inches="tight")
#         plt.close()
#     except Exception:
#         pass


# def _generate_timeline_chart(session: SessionData, path: str):
#     """Stylish dot-timeline chart."""
#     try:
#         fig, ax = plt.subplots(figsize=(8, 2.2))
#         fig.patch.set_facecolor(_mpl(COLOR_CARD))
#         ax.set_facecolor(_mpl(COLOR_CARD))

#         if not session.events:
#             ax.text(0.5, 0.5, "No events recorded",
#                     ha="center", va="center",
#                     color=_mpl(COLOR_MUTED), fontsize=11,
#                     transform=ax.transAxes)
#             ax.axis("off")
#         else:
#             session_start = session.start_time
#             times = [e.timestamp - session_start for e in session.events]
#             types = [getattr(e, "event_type", "event") for e in session.events]

#             # Baseline
#             total = max(times) if times else 1
#             ax.hlines(0, 0, total * 1.05, colors=_mpl(COLOR_BORDER),
#                       linewidth=1.5, zorder=1)

#             dot_colors = {
#                 "face_mismatch": _mpl(COLOR_RED),
#                 "liveness_fail": _mpl(COLOR_YELLOW),
#                 "multi_face":    _mpl(COLOR_ACCENT),
#                 "absence":       _mpl(COLOR_GREEN),
#             }
#             for t, tp in zip(times, types):
#                 c = dot_colors.get(tp, _mpl(COLOR_MUTED))
#                 ax.scatter(t, 0, color=c, s=60, zorder=3, edgecolors="white",
#                            linewidths=0.5)

#             # Legend
#             handles = [mpatches.Patch(color=v, label=k.replace("_", " ").title())
#                        for k, v in dot_colors.items()]
#             ax.legend(handles=handles, loc="upper right",
#                       fontsize=7, framealpha=0.2,
#                       labelcolor=_mpl(COLOR_WHITE),
#                       facecolor=_mpl(COLOR_BG))

#             ax.set_xlim(-total * 0.02, total * 1.07)
#             ax.set_xlabel("Time (seconds)", color=_mpl(COLOR_MUTED), fontsize=9)
#             ax.tick_params(axis="x", colors=_mpl(COLOR_MUTED), labelsize=8)
#             ax.set_yticks([])
#             for spine in ax.spines.values():
#                 spine.set_visible(False)

#         ax.set_title("Session Event Timeline", color=_mpl(COLOR_WHITE),
#                      fontsize=12, fontweight="bold", pad=8)
#         plt.tight_layout(pad=0.8)
#         plt.savefig(path, dpi=140, facecolor=fig.get_facecolor())
#         plt.close()
#     except Exception:
#         pass


# # ==============================
# # PDF CLASS
# # ==============================

# class SightFlowPDF(FPDF):

#     # ---- Page chrome ----

#     def header(self):
#         # Dark top bar
#         self.set_fill_color(*COLOR_BG)
#         self.rect(0, 0, 210, 18, "F")

#         # Accent left stripe
#         self.set_fill_color(*COLOR_ACCENT)
#         self.rect(0, 0, 4, 18, "F")

#         self.set_xy(8, 4)
#         self.set_font("Helvetica", "B", 13)
#         self.set_text_color(*COLOR_WHITE)
#         self.cell(0, 10, "SightFlow  |  AI Proctoring Report", ln=False)

#         # Right-align date
#         date_str = datetime.now().strftime("%d %b %Y  %H:%M")
#         self.set_font("Helvetica", "", 8)
#         self.set_text_color(*COLOR_MUTED)
#         self.set_xy(0, 6)
#         self.cell(202, 6, date_str, align="R")

#         self.ln(14)

#     def footer(self):
#         self.set_y(-12)
#         self.set_fill_color(*COLOR_BG)
#         self.rect(0, self.get_y() - 2, 210, 15, "F")
#         self.set_font("Helvetica", "I", 7)
#         self.set_text_color(*COLOR_MUTED)
#         self.cell(0, 8,
#                   f"SightFlow Compliance Report  |  Page {self.page_no()}  |  Confidential",
#                   align="C")

#     # ---- Section heading ----

#     def section_title(self, title: str):
#         self.ln(5)
#         safe = clean_text_for_pdf(str(title))

#         # Accent bar
#         self.set_fill_color(*COLOR_ACCENT)
#         self.rect(10, self.get_y(), 3, 7, "F")

#         self.set_xy(15, self.get_y())
#         self.set_font("Helvetica", "B", 11)
#         self.set_text_color(*COLOR_WHITE)
#         self.cell(0, 7, safe, ln=True)
#         self.ln(2)

#     # ---- Info card (key/value row) ----

#     def info_row(self, key: str, value: str, alt: bool = False):
#         safe_key   = clean_text_for_pdf(str(key))
#         safe_value = clean_text_for_pdf(str(value))

#         fill_color = COLOR_CARD if alt else COLOR_BG
#         self.set_fill_color(*fill_color)
#         self.set_x(10)
#         row_y = self.get_y()

#         self.set_fill_color(*fill_color)
#         self.rect(10, row_y, 190, 7, "F")

#         # Key
#         self.set_xy(13, row_y + 0.8)
#         self.set_font("Helvetica", "B", 9)
#         self.set_text_color(*COLOR_MUTED)
#         self.cell(55, 6, safe_key)

#         # Value
#         self.set_font("Helvetica", "", 9)
#         self.set_text_color(*COLOR_WHITE)
#         self.multi_cell(130, 6, safe_value)

#     # ---- Coloured badge ----

#     def badge(self, label: str, color: tuple):
#         safe = clean_text_for_pdf(str(label))
#         x, y = self.get_x(), self.get_y()
#         w = len(safe) * 2.5 + 8
#         self.set_fill_color(*color)
#         self.set_text_color(*COLOR_BG)
#         self.set_font("Helvetica", "B", 9)
#         self.rect(x, y, w, 7, "F")
#         self.set_xy(x + 2, y + 0.5)
#         self.cell(w - 4, 6, safe)
#         self.ln(9)

#     # ---- Body text ----

#     def body_text(self, text: str):
#         safe = clean_text_for_pdf(str(text))
#         self.set_x(10)
#         self.set_font("Helvetica", "", 9.5)
#         self.set_text_color(*COLOR_MUTED)
#         self.multi_cell(190, 6, safe)
#         self.ln(2)

#     # ---- Divider ----

#     def divider(self):
#         self.set_draw_color(*COLOR_BORDER)
#         self.line(10, self.get_y(), 200, self.get_y())
#         self.ln(3)


# # ==============================
# # MAIN FUNCTION
# # ==============================

# def generate_pdf_report(session: SessionData) -> str:
#     """
#     Generate stylish PDF compliance report.
#     Only uses fpdf2 + matplotlib – no extra dependencies.
#     """

#     # ---- Risk ----
#     try:
#         risk = calculate_risk_score(session)
#     except Exception:
#         risk = {"score": 0, "level": "Unknown", "breakdown": {}}

#     score = risk.get("score", 0)
#     level = risk.get("level", "Unknown")
#     summary_dict = session.to_summary_dict()

#     # ---- Charts ----
#     chart_risk     = f"/tmp/risk_{session.session_id}.png"
#     chart_gauge    = f"/tmp/gauge_{session.session_id}.png"
#     chart_timeline = f"/tmp/timeline_{session.session_id}.png"

#     _generate_risk_chart(session, chart_risk)
#     _generate_gauge_chart(score, level, chart_gauge)
#     _generate_timeline_chart(session, chart_timeline)

#     # ---- AI text ----
#     if LLM_AVAILABLE:
#         try:
#             ai_summary        = generate_session_summary(session)
#             ai_explanation    = generate_behavior_explanation(session)
#             ai_recommendation = generate_compliance_recommendation(session)
#         except Exception:
#             ai_summary        = "AI summary unavailable."
#             ai_explanation    = "AI explanation unavailable."
#             ai_recommendation = "Manual review recommended."
#     else:
#         ai_summary        = "AI module not installed."
#         ai_explanation    = "AI module not installed."
#         ai_recommendation = "Manual review recommended."

#     # ============================
#     # Build PDF
#     # ============================
#     pdf = SightFlowPDF()
#     pdf.set_margins(10, 10, 10)
#     pdf.set_auto_page_break(auto=True, margin=14)
#     pdf.add_page()

#     # Dark page background
#     pdf.set_fill_color(*COLOR_BG)
#     pdf.rect(0, 0, 210, 297, "F")

#     # ---- Session Info ----
#     pdf.section_title("Session Information")
#     rows = [
#         ("Session ID",      session.session_id),
#         ("Candidate",       session.candidate_name),
#         ("Start Time",      summary_dict.get("start_time", "-")),
#         ("End Time",        summary_dict.get("end_time", "-")),
#         ("Duration",        str(summary_dict.get("duration_seconds", "-")) + " sec"),
#         ("Frames Analyzed", str(session.total_frames)),
#     ]
#     for i, (k, v) in enumerate(rows):
#         pdf.info_row(k, v, alt=bool(i % 2))
#     pdf.ln(4)

#     # ---- Risk Assessment ----
#     pdf.section_title("Risk Assessment")

#     # Gauge + score side by side
#     gauge_x = 130
#     if os.path.exists(chart_gauge):
#         pdf.image(chart_gauge, x=gauge_x, y=pdf.get_y(), w=60)

#     score_y = pdf.get_y()
#     pdf.set_xy(13, score_y + 4)
#     pdf.set_font("Helvetica", "B", 36)
#     pdf.set_text_color(*_mpl_to_255(RISK_COLORS.get(level, COLOR_MUTED)))
#     pdf.cell(0, 14, f"{score}/100", ln=True)

#     pdf.set_x(13)
#     pdf.set_font("Helvetica", "", 10)
#     pdf.set_text_color(*COLOR_MUTED)
#     pdf.cell(0, 6, f"Risk Level:", ln=True)

#     pdf.set_x(13)
#     pdf.badge(level, RISK_COLORS.get(level, COLOR_MUTED))

#     pdf.ln(30)  # space below gauge

#     # ---- Risk Breakdown Chart ----
#     pdf.section_title("Risk Breakdown")
#     if os.path.exists(chart_risk):
#         pdf.image(chart_risk, x=10, w=178)
#     pdf.ln(3)

#     # ---- Timeline ----
#     pdf.section_title("Event Timeline")
#     if os.path.exists(chart_timeline):
#         pdf.image(chart_timeline, x=10, w=178)
#     pdf.ln(3)

#   # ---- Detected Cheating Objects ----
#     pdf.section_title("Detected Cheating Objects")
#     if not session.detected_objects:
#         pdf.body_text("No suspicious objects detected during this session.")
#     else:
#       # Deduplicate: group by label
#       from collections import Counter
#       label_counts = Counter(obj.label for obj in session.detected_objects)

#       summary_lines = []
#       for label, count in label_counts.items():
#           # Pick highest-confidence detection for this label
#           best = max(
#               (o for o in session.detected_objects if o.label == label),
#               key=lambda o: o.confidence,
#           )
#           # Format detection time relative to session start
#           rel_time = round(best.timestamp - session.start_time, 1)
#           summary_lines.append(
#               f"{label}  –  detected {count}x  "
#               f"(first at {rel_time}s, confidence {best.confidence:.0%})"
#           )

#     pdf.body_text("\n".join(summary_lines))

#       # Detailed table
#     pdf.ln(3)
#     col_w = [40, 35, 30, 30, 55]
#     headers = ["Object", "YOLO Class", "Confidence", "Frame #", "Time (s)"]
#     pdf.set_font("Helvetica", "B", 8)
#     pdf.set_text_color(148, 163, 184)
#     pdf.set_x(10)
#     for i, h in enumerate(headers):
#         pdf.cell(col_w[i], 6, h)
#     pdf.ln()

#     pdf.set_font("Helvetica", "", 8)
#     for det in session.detected_objects:
#         rel = round(det.timestamp - session.start_time, 1)
#         row = [
#             det.label,
#             det.raw_class,
#             f"{det.confidence:.0%}",
#             str(det.frame_index),
#             str(rel),
#         ]
#         alt = session.detected_objects.index(det) % 2
#         fill = (30, 41, 59) if alt else (15, 23, 42)
#         pdf.set_fill_color(*fill)
#         pdf.set_x(10)
#         for i, cell in enumerate(row):
#             pdf.set_text_color(255, 255, 255)
#             pdf.cell(col_w[i], 6, clean_text_for_pdf(cell), fill=True)
#         pdf.ln()








#     # ---- AI Insights ----
#     pdf.add_page()
#     # Re-apply dark background on new page
#     pdf.set_fill_color(*COLOR_BG)
#     pdf.rect(0, 0, 210, 297, "F")

#     pdf.section_title("AI Session Summary")
#     pdf.body_text(ai_summary)
#     pdf.divider()

#     pdf.section_title("Behaviour Analysis")
#     pdf.body_text(ai_explanation)
#     pdf.divider()

#     pdf.section_title("Compliance Recommendation")
#     pdf.body_text(ai_recommendation)

#     # ---- Save ----
#     out_path = os.path.join(REPORTS_DIR,
#                             f"sightflow_report_{session.session_id}.pdf")
#     try:
#         pdf.output(out_path)
#     except Exception as e:
#         raise RuntimeError(f"PDF generation failed: {str(e)}")

#     # Cleanup
#     for p in [chart_risk, chart_gauge, chart_timeline]:
#         try:
#             if os.path.exists(p):
#                 os.remove(p)
#         except Exception:
#             pass

#     return out_path


# # ==============================
# # Utility
# # ==============================

# def _mpl_to_255(rgb):
#     """Ensure RGB values are 0-255 integers (pass-through if already ints)."""
#     if isinstance(rgb[0], float):
#         return tuple(int(c * 255) for c in rgb)
#     return tuple(int(c) for c in rgb)



"""
PDF Report Generator for SightFlow sessions.
Stylish Production Version - uses only fpdf2 + matplotlib (no new dependencies)
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from fpdf import FPDF
from datetime import datetime
from collections import Counter

from backend.models.session import SessionData
from backend.services.risk_engine import calculate_risk_score

# Optional LLM imports (safe)
try:
    from backend.services.llm_analysis import (
        generate_session_summary,
        generate_behavior_explanation,
        generate_compliance_recommendation,
    )
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False


# ==============================
# Reports Folder
# ==============================
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


# ==============================
# Design Tokens
# ==============================
COLOR_BG     = (15,  23,  42)
COLOR_CARD   = (30,  41,  59)
COLOR_ACCENT = (99,  102, 241)
COLOR_GREEN  = (34,  197, 94)
COLOR_YELLOW = (234, 179, 8)
COLOR_RED    = (239, 68,  68)
COLOR_WHITE  = (255, 255, 255)
COLOR_MUTED  = (148, 163, 184)
COLOR_BORDER = (51,  65,  85)

RISK_COLORS = {
    "Low":      COLOR_GREEN,
    "Moderate": COLOR_YELLOW,
    "High":     COLOR_RED,
    "Critical": (220, 38,  38),
    "Unknown":  COLOR_MUTED,
}

def _hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def _mpl(rgb):
    return tuple(c / 255 for c in rgb)

def _mpl_to_255(rgb):
    """Ensure RGB values are 0-255 integers (pass-through if already ints)."""
    if isinstance(rgb[0], float):
        return tuple(int(c * 255) for c in rgb)
    return tuple(int(c) for c in rgb)


# ==============================
# Text Sanitiser
# ==============================

def clean_text_for_pdf(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u2013": "-", "\u2014": "-",
        "\u201C": '"', "\u201D": '"',
        "\u2018": "'", "\u2019": "'",
        "\u2022": "-", "\u00A0": " ", "\u202F": " ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "ignore").decode("latin-1")


# ==============================
# Chart Helpers
# ==============================

def _generate_risk_chart(session: SessionData, path: str):
    """Stylish horizontal bar chart."""
    try:
        risk = calculate_risk_score(session)
        bd   = risk.get("breakdown", {})

        labels = ["Face Mismatch", "Liveness Fail", "Multi Face", "Absence"]
        keys   = ["face_mismatch",  "liveness_fail",  "multi_face", "absence"]
        values = [bd.get(k, 0) for k in keys]
        bar_colors = [_mpl(COLOR_ACCENT), _mpl(COLOR_RED),
                      _mpl(COLOR_YELLOW), _mpl(COLOR_GREEN)]

        fig, ax = plt.subplots(figsize=(8, 3.2))
        fig.patch.set_facecolor(_mpl(COLOR_CARD))
        ax.set_facecolor(_mpl(COLOR_CARD))

        y_pos = np.arange(len(labels))
        bars  = ax.barh(y_pos, values, height=0.55,
                        color=bar_colors, edgecolor="none", zorder=3)

        ax.xaxis.grid(True, color=_mpl(COLOR_BORDER), linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)

        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_width() + 0.8,
                        bar.get_y() + bar.get_height() / 2,
                        str(val), va="center", ha="left",
                        color=_mpl(COLOR_WHITE), fontsize=9, fontweight="bold")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color=_mpl(COLOR_WHITE), fontsize=10)
        ax.tick_params(axis="x", colors=_mpl(COLOR_MUTED), labelsize=8)
        ax.set_xlim(0, max(max(values) + 15, 60))

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_title("Risk Score Breakdown", color=_mpl(COLOR_WHITE),
                     fontsize=12, fontweight="bold", pad=10)

        plt.tight_layout(pad=0.8)
        plt.savefig(path, dpi=140, facecolor=fig.get_facecolor())
        plt.close()
    except Exception:
        pass


def _generate_gauge_chart(score: int, level: str, path: str):
    """Semi-circle gauge for overall risk score."""
    try:
        fig, ax = plt.subplots(figsize=(4.5, 2.8), subplot_kw={"projection": "polar"})
        fig.patch.set_facecolor(_mpl(COLOR_CARD))
        ax.set_facecolor(_mpl(COLOR_CARD))

        theta_bg = np.linspace(np.pi, 0, 200)
        ax.plot(theta_bg, [1] * 200, linewidth=18,
                color=_mpl(COLOR_BORDER), solid_capstyle="round")

        fill_angle = np.pi * (1 - score / 100)
        theta_fg   = np.linspace(np.pi, fill_angle, 200)
        arc_color  = _mpl(RISK_COLORS.get(level, COLOR_MUTED))
        ax.plot(theta_fg, [1] * 200, linewidth=18,
                color=arc_color, solid_capstyle="round")

        ax.text(0, 0, f"{score}", ha="center", va="center",
                fontsize=28, fontweight="bold",
                color=_mpl(COLOR_WHITE), transform=ax.transData)
        ax.text(0, -0.35, level.upper(), ha="center", va="center",
                fontsize=10, color=arc_color, fontweight="bold",
                transform=ax.transData)

        ax.set_ylim(0, 1.3)
        ax.set_xlim(0, np.pi)
        ax.axis("off")
        ax.set_thetamin(0)
        ax.set_thetamax(180)

        plt.tight_layout(pad=0.2)
        plt.savefig(path, dpi=140, facecolor=fig.get_facecolor(),
                    bbox_inches="tight")
        plt.close()
    except Exception:
        pass


def _generate_timeline_chart(session: SessionData, path: str):
    """Stylish dot-timeline chart."""
    try:
        fig, ax = plt.subplots(figsize=(8, 2.2))
        fig.patch.set_facecolor(_mpl(COLOR_CARD))
        ax.set_facecolor(_mpl(COLOR_CARD))

        if not session.events:
            ax.text(0.5, 0.5, "No events recorded",
                    ha="center", va="center",
                    color=_mpl(COLOR_MUTED), fontsize=11,
                    transform=ax.transAxes)
            ax.axis("off")
        else:
            session_start = session.start_time
            times = [e.timestamp - session_start for e in session.events]
            types = [getattr(e, "event_type", "event") for e in session.events]

            total = max(times) if times else 1
            ax.hlines(0, 0, total * 1.05, colors=_mpl(COLOR_BORDER),
                      linewidth=1.5, zorder=1)

            dot_colors = {
                "face_mismatch": _mpl(COLOR_RED),
                "liveness_fail": _mpl(COLOR_YELLOW),
                "multi_face":    _mpl(COLOR_ACCENT),
                "absence":       _mpl(COLOR_GREEN),
            }
            for t, tp in zip(times, types):
                c = dot_colors.get(tp, _mpl(COLOR_MUTED))
                ax.scatter(t, 0, color=c, s=60, zorder=3,
                           edgecolors="white", linewidths=0.5)

            handles = [mpatches.Patch(color=v, label=k.replace("_", " ").title())
                       for k, v in dot_colors.items()]
            ax.legend(handles=handles, loc="upper right",
                      fontsize=7, framealpha=0.2,
                      labelcolor=_mpl(COLOR_WHITE),
                      facecolor=_mpl(COLOR_BG))

            ax.set_xlim(-total * 0.02, total * 1.07)
            ax.set_xlabel("Time (seconds)", color=_mpl(COLOR_MUTED), fontsize=9)
            ax.tick_params(axis="x", colors=_mpl(COLOR_MUTED), labelsize=8)
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)

        ax.set_title("Session Event Timeline", color=_mpl(COLOR_WHITE),
                     fontsize=12, fontweight="bold", pad=8)
        plt.tight_layout(pad=0.8)
        plt.savefig(path, dpi=140, facecolor=fig.get_facecolor())
        plt.close()
    except Exception:
        pass


def _generate_objects_chart(session: SessionData, path: str):
    """
    Bar chart showing how many times each cheating object was detected.
    Only saved when session.detected_objects is not empty.
    """
    try:
        detected = getattr(session, "detected_objects", [])
        if not detected:
            return

        counts = Counter(obj.label for obj in detected)
        labels = list(counts.keys())
        values = list(counts.values())

        palette = [
            _mpl(COLOR_RED), _mpl(COLOR_YELLOW), _mpl(COLOR_ACCENT),
            _mpl(COLOR_GREEN), (0.9, 0.5, 0.1), (0.5, 0.9, 0.8),
        ]
        bar_colors = [palette[i % len(palette)] for i in range(len(labels))]

        fig, ax = plt.subplots(figsize=(8, max(2.5, len(labels) * 0.7)))
        fig.patch.set_facecolor(_mpl(COLOR_CARD))
        ax.set_facecolor(_mpl(COLOR_CARD))

        y_pos = np.arange(len(labels))
        bars  = ax.barh(y_pos, values, height=0.5,
                        color=bar_colors, edgecolor="none", zorder=3)

        ax.xaxis.grid(True, color=_mpl(COLOR_BORDER), linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", ha="left",
                    color=_mpl(COLOR_WHITE), fontsize=9, fontweight="bold")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color=_mpl(COLOR_WHITE), fontsize=10)
        ax.tick_params(axis="x", colors=_mpl(COLOR_MUTED), labelsize=8)
        ax.set_xlim(0, max(values) + 2)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_title("Detected Cheating Objects - Count per Type",
                     color=_mpl(COLOR_WHITE), fontsize=12,
                     fontweight="bold", pad=10)

        plt.tight_layout(pad=0.8)
        plt.savefig(path, dpi=140, facecolor=fig.get_facecolor())
        plt.close()
    except Exception:
        pass


# ==============================
# PDF CLASS
# ==============================

class SightFlowPDF(FPDF):

    def header(self):
        self.set_fill_color(*COLOR_BG)
        self.rect(0, 0, 210, 18, "F")

        self.set_fill_color(*COLOR_ACCENT)
        self.rect(0, 0, 4, 18, "F")

        self.set_xy(8, 4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 10, "SightFlow  |  AI Proctoring Report", ln=False)

        date_str = datetime.now().strftime("%d %b %Y  %H:%M")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLOR_MUTED)
        self.set_xy(0, 6)
        self.cell(202, 6, date_str, align="R")

        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_fill_color(*COLOR_BG)
        self.rect(0, self.get_y() - 2, 210, 15, "F")
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*COLOR_MUTED)
        self.cell(
            0, 8,
            f"SightFlow Compliance Report  |  Page {self.page_no()}  |  Confidential",
            align="C",
        )

    def section_title(self, title: str):
        self.ln(5)
        safe = clean_text_for_pdf(str(title))

        self.set_fill_color(*COLOR_ACCENT)
        self.rect(10, self.get_y(), 3, 7, "F")

        self.set_xy(15, self.get_y())
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 7, safe, ln=True)
        self.ln(2)

    def info_row(self, key: str, value: str, alt: bool = False):
        safe_key   = clean_text_for_pdf(str(key))
        safe_value = clean_text_for_pdf(str(value))

        fill_color = COLOR_CARD if alt else COLOR_BG
        self.set_fill_color(*fill_color)
        row_y = self.get_y()
        self.rect(10, row_y, 190, 7, "F")

        self.set_xy(13, row_y + 0.8)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*COLOR_MUTED)
        self.cell(55, 6, safe_key)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(*COLOR_WHITE)
        self.multi_cell(130, 6, safe_value)

    def badge(self, label: str, color: tuple):
        safe = clean_text_for_pdf(str(label))
        x, y = self.get_x(), self.get_y()
        w = len(safe) * 2.5 + 8
        self.set_fill_color(*color)
        self.set_text_color(*COLOR_BG)
        self.set_font("Helvetica", "B", 9)
        self.rect(x, y, w, 7, "F")
        self.set_xy(x + 2, y + 0.5)
        self.cell(w - 4, 6, safe)
        self.ln(9)

    def body_text(self, text: str):
        safe = clean_text_for_pdf(str(text))
        self.set_x(10)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*COLOR_MUTED)
        self.multi_cell(190, 6, safe)
        self.ln(2)

    def divider(self):
        self.set_draw_color(*COLOR_BORDER)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)


# ==============================
# MAIN FUNCTION
# ==============================

def generate_pdf_report(session: SessionData) -> str:
    """
    Generate stylish PDF compliance report.
    Only uses fpdf2 + matplotlib - no extra dependencies.
    """

    # ---- Risk ----
    try:
        risk = calculate_risk_score(session)
    except Exception:
        risk = {"score": 0, "level": "Unknown", "breakdown": {}}

    score        = risk.get("score", 0)
    level        = risk.get("level", "Unknown")
    summary_dict = session.to_summary_dict()

    # ---- Charts ----
    chart_risk     = f"/tmp/risk_{session.session_id}.png"
    chart_gauge    = f"/tmp/gauge_{session.session_id}.png"
    chart_timeline = f"/tmp/timeline_{session.session_id}.png"
    chart_objects  = f"/tmp/objects_{session.session_id}.png"

    _generate_risk_chart(session, chart_risk)
    _generate_gauge_chart(score, level, chart_gauge)
    _generate_timeline_chart(session, chart_timeline)
    _generate_objects_chart(session, chart_objects)

    # ---- AI text ----
    if LLM_AVAILABLE:
        try:
            ai_summary        = generate_session_summary(session)
            ai_explanation    = generate_behavior_explanation(session)
            ai_recommendation = generate_compliance_recommendation(session)
        except Exception:
            ai_summary        = "AI summary unavailable."
            ai_explanation    = "AI explanation unavailable."
            ai_recommendation = "Manual review recommended."
    else:
        ai_summary        = "AI module not installed."
        ai_explanation    = "AI module not installed."
        ai_recommendation = "Manual review recommended."

    # ============================
    # Build PDF
    # ============================
    pdf = SightFlowPDF()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    # Dark page background
    pdf.set_fill_color(*COLOR_BG)
    pdf.rect(0, 0, 210, 297, "F")

    # ---- Session Info ----
    pdf.section_title("Session Information")
    rows = [
        ("Session ID",      session.session_id),
        ("Candidate",       session.candidate_name),
        ("Start Time",      summary_dict.get("start_time", "-")),
        ("End Time",        summary_dict.get("end_time", "-")),
        ("Duration",        str(summary_dict.get("duration_seconds", "-")) + " sec"),
        ("Frames Analyzed", str(session.total_frames)),
    ]
    for i, (k, v) in enumerate(rows):
        pdf.info_row(k, v, alt=bool(i % 2))
    pdf.ln(4)

    # ---- Risk Assessment ----
    pdf.section_title("Risk Assessment")

    if os.path.exists(chart_gauge):
        pdf.image(chart_gauge, x=130, y=pdf.get_y(), w=60)

    score_y = pdf.get_y()
    pdf.set_xy(13, score_y + 4)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*_mpl_to_255(RISK_COLORS.get(level, COLOR_MUTED)))
    pdf.cell(0, 14, f"{score}/100", ln=True)

    pdf.set_x(13)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(0, 6, "Risk Level:", ln=True)

    pdf.set_x(13)
    pdf.badge(level, RISK_COLORS.get(level, COLOR_MUTED))

    pdf.ln(30)

    # ---- Risk Breakdown Chart ----
    pdf.section_title("Risk Breakdown")
    if os.path.exists(chart_risk):
        pdf.image(chart_risk, x=10, w=178)
    pdf.ln(3)

    # ---- Timeline ----
    pdf.section_title("Event Timeline")
    if os.path.exists(chart_timeline):
        pdf.image(chart_timeline, x=10, w=178)
    pdf.ln(3)

    # ================================================================
    # ---- Detected Cheating Objects ----
    # ================================================================
    pdf.section_title("Detected Cheating Objects")

    # Use getattr so it works even if session.detected_objects is missing
    detected_objects = getattr(session, "detected_objects", [])

    if not detected_objects:
        # ── Nothing found – single safe path, no summary_lines needed ──
        pdf.body_text("No suspicious objects detected during this session.")

    else:
        # ── Build summary lines first, THEN call body_text ─────────────
        label_counts  = Counter(obj.label for obj in detected_objects)
        summary_lines = []

        for label, count in label_counts.items():
            best = max(
                (o for o in detected_objects if o.label == label),
                key=lambda o: o.confidence,
            )
            rel_time = round(best.timestamp - session.start_time, 1)
            summary_lines.append(
                f"{label}  -  detected {count}x  "
                f"(first at {rel_time}s, confidence {best.confidence:.0%})"
            )

        # summary_lines is guaranteed to exist here
        pdf.body_text("\n".join(summary_lines))

        # ── Objects bar chart ──────────────────────────────────────────
        if os.path.exists(chart_objects):
            pdf.image(chart_objects, x=10, w=178)
        pdf.ln(3)

        # ── Detailed table header ──────────────────────────────────────
        col_w   = [42, 38, 30, 28, 42]
        headers = ["Object", "YOLO Class", "Confidence", "Frame #", "Time (s)"]

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*COLOR_MUTED)
        pdf.set_x(10)
        for w, h in zip(col_w, headers):
            pdf.cell(w, 7, h)
        pdf.ln()

        # Separator line under header
        pdf.set_draw_color(*COLOR_BORDER)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(1)

        # ── Detailed table rows ────────────────────────────────────────
        pdf.set_font("Helvetica", "", 8)
        for idx, det in enumerate(detected_objects):
            rel  = round(det.timestamp - session.start_time, 1)
            row  = [
                det.label,
                det.raw_class,
                f"{det.confidence:.0%}",
                str(det.frame_index),
                str(rel),
            ]
            fill = COLOR_CARD if idx % 2 == 0 else COLOR_BG
            pdf.set_fill_color(*fill)
            pdf.set_x(10)
            for w, cell_text in zip(col_w, row):
                pdf.set_text_color(*COLOR_WHITE)
                pdf.cell(w, 6, clean_text_for_pdf(cell_text), fill=True)
            pdf.ln()

    # ---- AI Insights (new page) ----
    pdf.add_page()
    pdf.set_fill_color(*COLOR_BG)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.section_title("AI Session Summary")
    pdf.body_text(ai_summary)
    pdf.divider()

    pdf.section_title("Behaviour Analysis")
    pdf.body_text(ai_explanation)
    pdf.divider()

    pdf.section_title("Compliance Recommendation")
    pdf.body_text(ai_recommendation)

    # ---- Save ----
    out_path = os.path.join(
        REPORTS_DIR,
        f"sightflow_report_{session.session_id}.pdf",
    )
    try:
        pdf.output(out_path)
    except Exception as e:
        raise RuntimeError(f"PDF generation failed: {str(e)}")

    # Cleanup temp images
    for p in [chart_risk, chart_gauge, chart_timeline, chart_objects]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    return out_path