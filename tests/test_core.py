from datetime import date

from triage_tape.core import build_handoff, parse_notes


def test_parses_notes_and_reports_unknown_lines():
    items, warnings = parse_notes("[P1] blocked - OAuth callback fails @maya due:2026-10-01\nfreeform note")
    assert items[0].owner == "maya"
    assert items[0].state == "blocked"
    assert warnings == ["Line 2: couldn't read item"]


def test_handoff_prioritizes_active_work_and_flags_gaps():
    items, _ = parse_notes("[P2] watch - Error rate drifting @lee due:2026-10-09\n[P0] blocked - Payments fail due:2026-10-01\n[P1] done - Rolled back")
    report = build_handoff(items, "Checkout incident", date(2026, 10, 7))
    assert report.index("Payments fail") < report.index("Error rate drifting")
    assert "**1** blocked · **1** overdue · **1** without an owner" in report
    assert "## Closed since last handoff" in report


def test_empty_handoff_is_still_useful():
    report = build_handoff([], "Quiet shift", date(2026, 10, 7))
    assert "No active work. Nice handoff." in report
