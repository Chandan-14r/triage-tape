from datetime import date

import json

from triage_tape.core import build_handoff, build_handoff_json, parse_notes


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


def test_handoff_can_surface_shift_changes():
    previous, _ = parse_notes(
        "[P0] open - Payments fail @maya\n[P1] open - Inspect gateway logs @leo"
    )
    current, _ = parse_notes(
        "[P0] done - Payments fail @maya\n[P1] open - Inspect gateway logs @leo\n"
        "[P1] blocked - Confirm card issuer impact @sana"
    )
    report = build_handoff(current, "Checkout incident", date(2026, 10, 7), previous)
    assert "## Since the previous handoff" in report
    assert "### New work" in report
    assert "Confirm card issuer impact" in report
    assert "### No longer active" in report
    assert "Payments fail — completed" in report


def test_handoff_reports_when_a_shift_has_no_active_changes():
    previous, _ = parse_notes("[P1] open - Inspect gateway logs @leo")
    current, _ = parse_notes("[P1] watch - Inspect gateway logs @leo")
    report = build_handoff(current, "Checkout incident", date(2026, 10, 7), previous)
    assert "No active-work changes since the previous handoff." in report


def test_json_handoff_is_sorted_and_reports_machine_readable_shift_changes():
    previous, _ = parse_notes("[P0] open - Payments fail @maya")
    current, _ = parse_notes(
        "[P2] open - Watch dashboard @leo\n[P0] done - Payments fail @maya\n"
        "[P1] blocked - Confirm issuer impact"
    )
    payload = json.loads(build_handoff_json(current, "Checkout incident", date(2026, 10, 7), previous))
    assert payload["summary"] == {"active": 2, "blocked": 1, "overdue": 0, "unowned": 1, "closed": 1}
    assert [item["summary"] for item in payload["active_items"]] == ["Confirm issuer impact", "Watch dashboard"]
    assert payload["changes_since_previous"]["no_longer_active"][0]["outcome"] == "completed"
