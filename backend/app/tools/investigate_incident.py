
from app.graph.connection import create_db_connection


def investigate_incident(incident_id: str) -> dict:
    """Retrieve incident details, affected systems, resolver, and evidence."""
    incident_id = incident_id.strip()

    if not incident_id:
        return {
            "found": False,
            "incident_id": incident_id,
            "message": "Incident ID cannot be empty.",
        }

    _, graph = create_db_connection()

    result = graph.query(
        """
        MATCH (i:Incident {id: $incident_id})
        RETURN i.id, i.name, i.description, i.severity,
               i.status, i.occurred_at
        """,
        {"incident_id": incident_id},
    )

    if not result.result_set:
        return {
            "found": False,
            "incident_id": incident_id,
            "message": "Incident not found.",
        }

    row = result.result_set[0]

    affected_result = graph.query(
        """
        MATCH (i:Incident {id: $incident_id})-[:AFFECTED]->(s:System)
        RETURN s.id, s.name, s.criticality
        ORDER BY s.name
        """,
        {"incident_id": incident_id},
    )

    resolver_result = graph.query(
        """
        MATCH (p:Person)-[:RESOLVED]->(i:Incident {id: $incident_id})
        RETURN p.id, p.name
        ORDER BY p.name
        """,
        {"incident_id": incident_id},
    )

    document_result = graph.query(
        """
        MATCH (doc:Document)-[:DESCRIBES]->(i:Incident {id: $incident_id})
        RETURN doc.id, doc.name, doc.title, doc.description
        ORDER BY doc.id
        """,
        {"incident_id": incident_id},
    )

    return {
        "found": True,
        "incident": {
            "incident_id": row[0],
            "name": row[1],
            "description": row[2],
            "severity": row[3],
            "status": row[4],
            "occurred_at": row[5],
        },
        "affected_systems": [
            {
                "system_id": item[0],
                "system_name": item[1],
                "criticality": item[2],
            }
            for item in affected_result.result_set
        ],
        "resolvers": [
            {"person_id": item[0], "person_name": item[1]}
            for item in resolver_result.result_set
        ],
        "supporting_documents": [
            {
                "document_id": item[0],
                "document_name": item[1],
                "document_title": item[2],
                "description": item[3],
            }
            for item in document_result.result_set
        ],
    }
