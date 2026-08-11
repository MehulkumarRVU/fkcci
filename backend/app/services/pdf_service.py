"""Builds PDF reports using reportlab (pure-Python, no system binary
dependencies - avoids the wkhtmltopdf/Pango setup weasyprint would need).
Each builder returns raw PDF bytes; routes wrap that in a Response with
media_type="application/pdf".
"""
import io
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

_styles = getSampleStyleSheet()
_title_style = ParagraphStyle("ReportTitle", parent=_styles["Title"], textColor=colors.HexColor("#2563eb"))
_heading_style = ParagraphStyle("ReportHeading", parent=_styles["Heading2"], textColor=colors.HexColor("#1e40af"))
_body_style = _styles["BodyText"]
_muted_style = ParagraphStyle("Muted", parent=_styles["BodyText"], textColor=colors.HexColor("#6b7280"), fontSize=9)


def _fmt(value: Optional[float]) -> str:
    return "N/A" if value is None else f"{value:.1f}"


def _stat_table(rows: List[List[str]]) -> Table:
    table = Table(rows, colWidths=[2.4 * inch, 2.4 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def build_session_report(session: Any, athlete: Any) -> bytes:
    """A single completed session's report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="PocketCoach AI - Session Report")
    story = [
        Paragraph("PocketCoach AI - Session Report", _title_style),
        Spacer(1, 6),
        Paragraph(f"Athlete: {athlete.username}", _body_style),
        Paragraph(f"Sport: {session.sport_type} &nbsp;|&nbsp; Skill: {session.skill_name or 'N/A'}", _body_style),
        Paragraph(f"Date: {session.start_time.strftime('%Y-%m-%d %H:%M') if session.start_time else 'N/A'}", _muted_style),
        Spacer(1, 16),
        Paragraph("Scores", _heading_style),
        _stat_table([
            ["Metric", "Score"],
            ["Overall Performance", _fmt(session.performance_score)],
            ["Technique Accuracy", _fmt(session.technique_accuracy)],
            ["Reaction Score", _fmt(session.reaction_score)],
            ["Balance Score", _fmt(session.balance_score)],
            ["Duration (minutes)", str(session.duration_minutes or 0)],
        ]),
        Spacer(1, 16),
        Paragraph(f"Scoring engine: {session.scoring_version or 'v1'}", _muted_style),
    ]

    if session.joint_summary:
        story.append(Spacer(1, 16))
        story.append(Paragraph("Joint Deviation Summary", _heading_style))
        rows = [["Joint", "Low", "Medium", "High"]]
        for joint, counts in session.joint_summary.items():
            rows.append([str(joint), str(counts.get("low", 0)), str(counts.get("medium", 0)), str(counts.get("high", 0))])
        table = Table(rows, colWidths=[1.6 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        story.append(table)

    doc.build(story)
    return buffer.getvalue()


def build_progress_report(athlete: Any, twin_data: Dict[str, Any], stats: Dict[str, Any]) -> bytes:
    """An athlete's own progress report, reusing profile_twin_service data -
    no new aggregation logic."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="PocketCoach AI - Progress Report")
    story = [
        Paragraph("PocketCoach AI - Progress Report", _title_style),
        Spacer(1, 6),
        Paragraph(f"Athlete: {athlete.username}", _body_style),
        Paragraph(f"Skill level: {athlete.skill_level} &nbsp;|&nbsp; Active sport: {athlete.sport_type}", _body_style),
        Spacer(1, 16),
        Paragraph("Overview", _heading_style),
        _stat_table([
            ["Metric", "Value"],
            ["Total Sessions", str(stats.get("total_sessions", 0))],
            ["Total Training Minutes", str(stats.get("total_minutes", 0))],
            ["Avg Performance", _fmt(stats.get("average_performance"))],
            ["Avg Technique", _fmt(stats.get("average_technique"))],
            ["Avg Reaction", _fmt(stats.get("average_reaction"))],
            ["Avg Balance", _fmt(stats.get("average_balance"))],
            ["Current Streak (days)", str(athlete.current_streak or 0)],
            ["Longest Streak (days)", str(athlete.longest_streak or 0)],
        ]),
    ]

    per_sport = twin_data.get("per_sport") or {}
    if per_sport:
        story.append(Spacer(1, 16))
        story.append(Paragraph("Per-Sport Averages", _heading_style))
        rows = [["Sport", "Sessions", "Avg Score", "Trend"]]
        for sport, s in per_sport.items():
            rows.append([sport, str(s["session_count"]), _fmt(s["avg_score"]), s["trend_direction"]])
        table = Table(rows, colWidths=[1.6 * inch, 1.2 * inch, 1.2 * inch, 1.6 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        story.append(table)

    tendencies = twin_data.get("recurring_tendencies") or []
    if tendencies:
        story.append(Spacer(1, 16))
        story.append(Paragraph("Recurring Tendencies", _heading_style))
        for t in tendencies:
            story.append(Paragraph(
                f"&bull; {t['joint']}: {t['high_count']} high-deviation, {t['medium_count']} medium-deviation frames",
                _body_style,
            ))

    doc.build(story)
    return buffer.getvalue()


def build_coach_athlete_report(report: Any) -> bytes:
    """A coach's monthly report for one of their athletes, built from the
    exact same AthleteReport data build_athlete_monthly_report() already
    computes (backend/app/routes/analytics.py) - not re-queried here."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="PocketCoach AI - Coach Report")
    ms = report.monthly_stats
    story = [
        Paragraph("PocketCoach AI - Coach Report", _title_style),
        Spacer(1, 6),
        Paragraph(f"Athlete: {report.athlete_username}", _body_style),
        Paragraph(f"Sport: {report.sport_type} &nbsp;|&nbsp; Skill level: {report.skill_level}", _body_style),
        Spacer(1, 16),
        Paragraph("Last 30 Days", _heading_style),
        _stat_table([
            ["Metric", "Value"],
            ["Sessions (30d)", str(ms.total_sessions)],
            ["Completed Sessions", str(ms.completed_sessions)],
            ["Avg Performance", _fmt(ms.avg_performance_score)],
            ["Avg Technique", _fmt(ms.avg_technique_accuracy)],
            ["Avg Reaction", _fmt(ms.avg_reaction_score)],
            ["Avg Balance", _fmt(ms.avg_balance_score)],
            ["Highest Score", _fmt(ms.highest_performance)],
            ["Lowest Score", _fmt(ms.lowest_performance)],
            ["Training Hours (30d)", str(ms.total_training_hours)],
        ]),
    ]

    if report.recent_sessions:
        story.append(Spacer(1, 16))
        story.append(Paragraph("Recent Sessions", _heading_style))
        rows = [["Date", "Sport", "Type", "Performance", "Status"]]
        for s in report.recent_sessions[:10]:
            rows.append([
                s.start_time.strftime("%Y-%m-%d"),
                s.sport_type,
                s.session_type,
                _fmt(s.performance_score),
                "Completed" if s.is_completed else "In Progress",
            ])
        table = Table(rows, colWidths=[1.1 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(table)

    doc.build(story)
    return buffer.getvalue()
