
from app.graph.connection import create_db_connection


def get_owner(system_id: str) -> dict:
    """
    Return a system's current owner and ownership history.

    An OWNS relationship is current when valid_to is NULL.
    """
    _, graph = create_db_connection()

    query = """
    MATCH (s:System {id: $system_id})
    OPTIONAL MATCH (t:Team)-[r:OWNS]->(s)
    RETURN
        s.id AS system_id,
        s.name AS system_name,
        s.criticality AS criticality,
        t.name AS owner,
        r.valid_from AS valid_from,
        r.valid_to AS valid_to,
        r.source_id AS source_id
    ORDER BY r.valid_from
    """

    result = graph.query(query, {"system_id": system_id})

    if not result.result_set:
        return {
            "found": False,
            "system_id": system_id,
            "message": "System not found.",
        }

    rows = result.result_set
    system = {
        "system_id": rows[0][0],
        "system_name": rows[0][1],
        "criticality": rows[0][2],
    }

    ownership_history = []
    current_owner = None

    for row in rows:
        _, _, _, owner, valid_from, valid_to, source_id = row

        if owner is None:
            continue

        ownership = {
            "owner": owner,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "source_id": source_id,
        }
        ownership_history.append(ownership)

        if valid_to is None:
            current_owner = ownership

    return {
        "found": True,
        **system,
        "current_owner": current_owner,
        "ownership_history": ownership_history,
    }
