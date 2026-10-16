
from app.graph.connection import create_db_connection


# Fixed labels and relationship types: never taken from user input.
NODES = [
    ("Team", {
        "id": "team_payments",
        "name": "Payments Platform",
        "description": "Owns payment processing and transaction services",
    }),
    ("Team", {
        "id": "team_infra_sre",
        "name": "Infrastructure & SRE",
        "description": "Owns reliability and operational infrastructure",
    }),
    ("Person", {
        "id": "person_aditi",
        "name": "Aditi Sharma",
        "role": "Senior Backend Engineer",
        "active": True,
    }),
    ("Person", {
        "id": "person_rohan",
        "name": "Rohan Mehta",
        "role": "Backend Engineer",
        "active": True,
    }),
    ("Person", {
        "id": "person_neha",
        "name": "Neha Kulkarni",
        "role": "SRE Engineer",
        "active": True,
    }),
    ("System", {
        "id": "sys_payment_gateway",
        "name": "Payment Gateway",
        "description": "Processes payment requests",
        "criticality": "critical",
        "status": "active",
    }),
    ("System", {
        "id": "sys_transaction_service",
        "name": "Transaction Service",
        "description": "Coordinates payment transactions",
        "criticality": "critical",
        "status": "active",
    }),
    ("System", {
        "id": "sys_ledger_service",
        "name": "Ledger Service",
        "description": "Records financial transactions",
        "criticality": "critical",
        "status": "active",
    }),
    ("Project", {
        "id": "proj_payment_modernization",
        "name": "Payment Modernization",
        "description": "Improves payment processing architecture",
        "status": "active",
    }),
    ("Technology", {
        "id": "tech_postgresql",
        "name": "PostgreSQL",
        "category": "database",
    }),
    ("Document", {
        "id": "doc_transaction_rfc",
        "title": "Transaction Service Database Architecture RFC",
        "source_type": "architecture_rfc",
        "source_uri": "synthetic://docs/transaction-service-rfc",
        "created_at": "2026-01-12",
        "summary": (
            "Synthetic architecture document comparing database "
            "options for the Transaction Service."
        ),
    }),
    ("Decision", {
        "id": "decision_postgres",
        "title": "Adopt PostgreSQL for Transaction Service",
        "rationale": (
            "The fictional architecture review selected PostgreSQL "
            "for relational consistency and transaction support."
        ),
        "decided_at": "2026-01-15",
        "status": "approved",
    }),
]


# source label, relationship type, target label, source ID, target ID,
# relationship properties
RELATIONSHIPS = [
    ("Person", "MEMBER_OF", "Team",
     "person_aditi", "team_payments", {}),
    ("Person", "MEMBER_OF", "Team",
     "person_rohan", "team_payments", {}),
    ("Person", "MEMBER_OF", "Team",
     "person_neha", "team_infra_sre", {}),

    ("Person", "WORKED_ON", "Project",
     "person_aditi", "proj_payment_modernization", {}),
    ("Person", "WORKED_ON", "Project",
     "person_rohan", "proj_payment_modernization", {}),

    ("Person", "AUTHORED", "Document",
     "person_aditi", "doc_transaction_rfc", {}),

    ("Team", "OWNS", "Project",
     "team_payments", "proj_payment_modernization", {}),

    ("Team", "OWNS", "System",
     "team_payments", "sys_transaction_service", {
         "valid_from": "2026-01-01",
         "valid_to": None,
         "source_id": "doc_transaction_rfc",
         "change_set_id": "seed_initial",
     }),

    # Historical ownership: effective through June 30.
    # valid_to is exclusive, so the boundary is July 1.
    ("Team", "OWNS", "System",
     "team_payments", "sys_payment_gateway", {
         "valid_from": "2026-01-01",
         "valid_to": "2026-07-01",
         "source_id": "doc_transaction_rfc",
         "change_set_id": "seed_initial",
     }),

    # Current ownership, effective from July 1 onward.
    ("Team", "OWNS", "System",
     "team_infra_sre", "sys_payment_gateway", {
         "valid_from": "2026-07-01",
         "valid_to": None,
         "source_id": "doc_transaction_rfc",
         "change_set_id": "seed_initial",
     }),

    ("Project", "USES", "System",
     "proj_payment_modernization", "sys_payment_gateway", {}),
    ("Project", "USES", "System",
     "proj_payment_modernization", "sys_transaction_service", {}),
    ("Project", "USES", "Technology",
     "proj_payment_modernization", "tech_postgresql", {}),

    ("System", "DEPENDS_ON", "System",
     "sys_payment_gateway", "sys_transaction_service", {}),
    ("System", "DEPENDS_ON", "System",
     "sys_transaction_service", "sys_ledger_service", {}),

    ("Document", "DESCRIBES", "System",
     "doc_transaction_rfc", "sys_transaction_service", {}),

    ("Person", "MADE", "Decision",
     "person_aditi", "decision_postgres", {}),
    ("Decision", "CHOOSES", "Technology",
     "decision_postgres", "tech_postgresql", {}),
    ("Decision", "AFFECTS", "System",
     "decision_postgres", "sys_transaction_service", {}),
    ("Decision", "SUPPORTED_BY", "Document",
     "decision_postgres", "doc_transaction_rfc", {}),
]


def create_node(graph, label, properties):
    query = f"""
    MERGE (n:{label} {{id: $id}})
    SET n += $properties
    """
    graph.query(query, {
        "id": properties["id"],
        "properties": properties,
    })


def create_relationship(
    graph, source_label, rel_type, target_label,
    source_id, target_id, properties
):
    if rel_type == "OWNS" and "valid_from" in properties:
        # valid_from is part of the identity of a historical period.
        query = f"""
        MATCH (a:{source_label} {{id: $source_id}})
        MATCH (b:{target_label} {{id: $target_id}})
        MERGE (a)-[r:{rel_type} {{valid_from: $valid_from}}]->(b)
        SET r += $properties
        """
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "valid_from": properties["valid_from"],
            "properties": properties,
        }
    else:
        query = f"""
        MATCH (a:{source_label} {{id: $source_id}})
        MATCH (b:{target_label} {{id: $target_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        """
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties,
        }

    result = graph.query(query, params)

    # A missing endpoint means the seed is inconsistent.
    # Verify relationship creation rather than silently skipping it.
    check = graph.query(
        f"""
        MATCH (a:{source_label} {{id: $source_id}})
              -[r:{rel_type}]->(b:{target_label} {{id: $target_id}})
        RETURN count(r) AS relationship_count
        """,
        {"source_id": source_id, "target_id": target_id},
    )

    if not check.result_set or check.result_set[0][0] < 1:
        raise RuntimeError(
            f"Failed to create {source_label}-[{rel_type}]->{target_label}: "
            f"{source_id} -> {target_id}"
        )


def seed_graph(graph):
    print("Seeding NovaTech nodes...")

    for label, properties in NODES:
        create_node(graph, label, properties)

    print("Seeding NovaTech relationships...")

    for relationship in RELATIONSHIPS:
        create_relationship(graph, *relationship)

    node_result = graph.query(
        "MATCH (n) RETURN count(n) AS total"
    )
    edge_result = graph.query(
        "MATCH ()-[r]->() RETURN count(r) AS total"
    )

    print(f"Total nodes: {node_result.result_set[0][0]}")
    print(f"Total relationships: {edge_result.result_set[0][0]}")
    print("NovaTech seed completed.")


def main():
    db, graph = create_db_connection()

    try:
        seed_graph(graph)
    finally:
        db.close()


if __name__ == "__main__":
    main()
