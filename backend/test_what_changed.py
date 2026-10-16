
import pytest

from app.tools.what_changed import what_changed


def test_all_ownership_events():
    result = what_changed()

    assert result["found"] is True
    assert result["change_count"] > 0

    events = result["changes"]

    assert any(
        event["system_name"] == "Payment Gateway"
        and event["team_name"] == "Payments Platform"
        and event["change_type"] == "ownership_ended"
        and event["date"] == "2026-07-01"
        for event in events
    )

    assert any(
        event["system_name"] == "Payment Gateway"
        and event["team_name"] == "Infrastructure & SRE"
        and event["change_type"] == "ownership_started"
        and event["date"] == "2026-07-01"
        for event in events
    )


def test_date_filter():
    result = what_changed(
        start_date="2026-07-01",
        end_date="2026-07-01",
    )

    assert result["found"] is True
    assert all(event["date"] == "2026-07-01" for event in result["changes"])


def test_invalid_date():
    with pytest.raises(ValueError):
        what_changed(start_date="01-07-2026")


def test_reversed_date_range():
    with pytest.raises(ValueError):
        what_changed(
            start_date="2026-07-02",
            end_date="2026-07-01",
        )


def test_date_with_no_changes():
    result = what_changed(
        start_date="2027-01-01",
        end_date="2027-01-31",
    )

    assert result["found"] is False
    assert result["changes"] == []
