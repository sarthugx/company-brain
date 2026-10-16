
from datetime import date

from app.graph.connection import create_db_connection


def what_changed(start_date: str | None = None,
                 end_date: str | None = None) -> dict:
    """Report ownership start/end events recorded in the graph.

    Dates are inclusive and use YYYY-MM-DD. With no dates, return all
    ownership events present in the graph.
    """
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None:
            try:
                parsed = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{name} must use YYYY-MM-DD format") from exc

            if parsed.isoformat() != value:
                raise ValueError(f"{name} must use YYYY-MM-DD format")

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    _, graph = create_db_connection()

    result = graph.query(
        """
        MATCH (t:Team)-[r:OWNS]->(s:System)
        RETURN
            t.id AS team_id,
            t.name AS team_name,
            s.id AS system_id,
            s.name AS system_name,
            r.valid_from AS valid_from,
            r.valid_to AS valid_to,
            r.source_id AS source_id
        ORDER BY r.valid_from, s.name
        """
    )

    events = []

    for row in result.result_set:
        team_id, team_name, system_id, system_name, valid_from, valid_to, source_id = row

        if valid_from:
            events.append({
                "date": valid_from,
                "change_type": "ownership_started",
                "team_id": team_id,
                "team_name": team_name,
                "system_id": system_id,
                "system_name": system_name,
                "source_id": source_id,
            })

        if valid_to:
            events.append({
                "date": valid_to,
                "change_type": "ownership_ended",
                "team_id": team_id,
                "team_name": team_name,
                "system_id": system_id,
                "system_name": system_name,
                "source_id": source_id,
            })

    if start_date:
        events = [event for event in events if event["date"] >= start_date]

    if end_date:
        events = [event for event in events if event["date"] <= end_date]

    events.sort(key=lambda event: (event["date"], event["system_name"], event["change_type"]))

    return {
        "found": bool(events),
        "start_date": start_date,
        "end_date": end_date,
        "change_count": len(events),
        "changes": events,
    }
