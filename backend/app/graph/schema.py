
from app.graph.connection import create_db_connection


# Core Company Brain node types.
NODE_LABELS = (
    "Person",
    "Team",
    "Project",
    "System",
    "Technology",
    "Document",
    "Decision",
    "Incident",
)


# Index properties used for entity lookup.
# Every entity has a stable ID.
NODE_INDEXES = {
    "Person": ("id", "name"),
    "Team": ("id", "name"),
    "Project": ("id", "name"),
    "System": ("id", "name"),
    "Technology": ("id", "name"),
    "Document": ("id", "title"),
    "Decision": ("id", "title"),
    "Incident": ("id", "title"),
}


# Relationship directions: source -> relationship -> target.
RELATIONSHIPS = {
    "MEMBER_OF": ("Person", "Team"),
    "MANAGES": ("Person", "Team"),
    "WORKED_ON": ("Person", "Project"),
    "AUTHORED": ("Person", "Document"),
    "RESOLVED": ("Person", "Incident"),
    "OWNS": ("Team", "System or Project"),
    "USES": ("Project", "System or Technology"),
    "DEPENDS_ON": ("System", "System"),
    "DESCRIBES": ("Document", "System or Incident"),
    "RELATES_TO": ("Document", "Project"),
    "MADE": ("Person", "Decision"),
    "CHOOSES": ("Decision", "Technology"),
    "AFFECTS": ("Decision", "System or Project"),
    "SUPPORTED_BY": ("Decision", "Document"),
    "AFFECTED": ("Incident", "System"),
    "RELATED_TO": ("Incident", "Project or Decision"),
}


def initialize_schema(graph):
    """Create indexes required for Company Brain entity lookups."""
    print("Initializing Company Brain graph indexes...")

    for label, properties in NODE_INDEXES.items():
        for property_name in properties:
            try:
                graph.create_node_range_index(label, property_name)
                print(f"Created index: {label}.{property_name}")

            except Exception as exc:
                message = str(exc).lower()

                # Allow rerunning initialization if an index already exists.
                if (
                    "already exists" in message
                    or "already indexed" in message
                    or "index already" in message
                ):
                    print(
                        f"Index already exists: "
                        f"{label}.{property_name}"
                    )
                else:
                    raise

    print("Schema index initialization complete.")


def main():
    db, graph = create_db_connection()

    try:
        initialize_schema(graph)

        result = graph.query(
            "MATCH (n) RETURN count(n) AS node_count"
        )
        node_count = result.result_set[0][0]

        print(f"Graph selected: {graph.name}")
        print(f"Current node count: {node_count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
