
from app.graph.connection import create_db_connection


def find_experts(topic: str) -> dict:
    """Find people with direct graph evidence related to a topic."""
    topic = topic.strip()
    if not topic:
        return {"found": False, "topic": topic, "experts": []}

    _, graph = create_db_connection()

    query = """
    MATCH (p:Person)-[r]->(target)
    WHERE (
        (type(r) = 'WORKED_ON' AND target:Project)
        OR (type(r) = 'RESOLVED' AND target:Incident)
        OR (type(r) = 'AUTHORED' AND target:Document)
    )
    AND (
        toLower(coalesce(target.name, '')) CONTAINS toLower($topic)
        OR toLower(coalesce(target.id, '')) CONTAINS toLower($topic)
        OR toLower(coalesce(target.description, '')) CONTAINS toLower($topic)
    )
    RETURN
        p.id AS person_id,
        p.name AS person_name,
        type(r) AS relationship,
        labels(target) AS evidence_type,
        target.id AS evidence_id,
        target.name AS evidence_name
    ORDER BY p.name
    """

    result = graph.query(query, {"topic": topic})
    experts = [
        {
            "person_id": row[0],
            "person_name": row[1],
            "relationship": row[2],
            "evidence_type": row[3],
            "evidence_id": row[4],
            "evidence_name": row[5],
        }
        for row in result.result_set
    ]

    return {
        "found": bool(experts),
        "topic": topic,
        "experts": experts,
    }
