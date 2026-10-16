
from app.graph.connection import create_db_connection

_, graph = create_db_connection()

queries = [
    ("Basic MATCH", "MATCH (n) RETURN count(n) AS node_count"),
    ("Team nodes", "MATCH (t:Team) RETURN t.name LIMIT 5"),
    (
        "Ownership relationships",
        "MATCH (t:Team)-[r:OWNS]->(s:System) RETURN t, r, s LIMIT 5",
    ),
]

for name, query in queries:
    print(f"\n--- {name} ---")
    try:
        result = graph.query(query)
        print(result.result_set)
    except Exception as error:
        print(f"{type(error).__name__}: {error}")

