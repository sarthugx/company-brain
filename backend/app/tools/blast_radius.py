
from app.graph.connection import create_db_connection


def blast_radius(system_id: str, max_depth: int = 5) -> dict:
    """Find systems that depend directly or indirectly on a given system."""
    system_id = system_id.strip()

    if not system_id:
        return {
            "found": False,
            "system_id": system_id,
            "affected_systems": [],
        }

    if not 1 <= max_depth <= 5:
        raise ValueError("max_depth must be between 1 and 5")

    _, graph = create_db_connection()

    system_result = graph.query(
        """
        MATCH (s:System {id: $system_id})
        RETURN s.id, s.name, s.criticality
        """,
        {"system_id": system_id},
    )

    if not system_result.result_set:
        return {
            "found": False,
            "system_id": system_id,
            "affected_systems": [],
        }

    _, system_name, criticality = system_result.result_set[0]

    dependency_query = f"""
    MATCH path = (target:System {{id: $system_id}})
             -[:DEPENDS_ON*1..{max_depth}]->
             (dependent:System)
    RETURN DISTINCT
        dependent.id AS system_id,
        dependent.name AS system_name,
        dependent.criticality AS criticality,
        length(path) AS dependency_depth
    ORDER BY dependency_depth, system_name
    """

    result = graph.query(dependency_query, {"system_id": system_id})

    affected_systems = [
        {
            "system_id": row[0],
            "system_name": row[1],
            "criticality": row[2],
            "dependency_depth": row[3],
        }
        for row in result.result_set
    ]

    return {
        "found": True,
        "target_system": {
            "system_id": system_id,
            "system_name": system_name,
            "criticality": criticality,
        },
        "affected_count": len(affected_systems),
        "affected_systems": affected_systems,
    }
