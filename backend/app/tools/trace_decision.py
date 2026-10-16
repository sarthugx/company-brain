
from app.graph.connection import create_db_connection


def trace_decision(decision_id: str) -> dict:
    """Trace a decision to its maker, chosen technology, affected entities,
    and supporting documents in the company knowledge graph.
    """
    decision_id = decision_id.strip()

    if not decision_id:
        return {
            "found": False,
            "decision_id": decision_id,
            "message": "Decision ID cannot be empty.",
        }

    _, graph = create_db_connection()

    decision_result = graph.query(
        """
        MATCH (d:Decision {id: $decision_id})
        RETURN d.id, d.name
        """,
        {"decision_id": decision_id},
    )

    if not decision_result.result_set:
        return {
            "found": False,
            "decision_id": decision_id,
            "message": "Decision not found.",
        }

    row = decision_result.result_set[0]
    decision = {
        "decision_id": row[0],
        "decision_name": row[1] or row[0],
    }

    maker_result = graph.query(
        """
        MATCH (p:Person)-[:MADE]->(d:Decision {id: $decision_id})
        RETURN p.id, p.name
        ORDER BY p.name
        """,
        {"decision_id": decision_id},
    )

    technology_result = graph.query(
        """
        MATCH (d:Decision {id: $decision_id})-[:CHOOSES]->(t:Technology)
        RETURN t.id, t.name
        ORDER BY t.name
        """,
        {"decision_id": decision_id},
    )

    affected_result = graph.query(
        """
        MATCH (d:Decision {id: $decision_id})-[:AFFECTS]->(target)
        RETURN target.id, labels(target), target.name
        ORDER BY target.name
        """,
        {"decision_id": decision_id},
    )

    document_result = graph.query(
        """
        MATCH (d:Decision {id: $decision_id})-[:SUPPORTED_BY]->(doc:Document)
        RETURN doc.id, doc.name, doc.title
        ORDER BY doc.id
        """,
        {"decision_id": decision_id},
    )

    return {
        "found": True,
        **decision,
        "made_by": [
            {"person_id": r[0], "person_name": r[1]}
            for r in maker_result.result_set
        ],
        "chosen_technologies": [
            {"technology_id": r[0], "technology_name": r[1]}
            for r in technology_result.result_set
        ],
        "affected_entities": [
            {"entity_id": r[0], "entity_type": r[1], "entity_name": r[2]}
            for r in affected_result.result_set
        ],
        "supporting_documents": [
            {
                "document_id": r[0],
                "document_name": r[1],
                "document_title": r[2],
            }
            for r in document_result.result_set
        ],
    }

