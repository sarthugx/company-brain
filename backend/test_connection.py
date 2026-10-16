import os

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

host = os.getenv("FALKORDB_HOST", "localhost")
port = int(os.getenv("FALKORDB_PORT", "6379"))
graph_name = os.getenv("FALKORDB_GRAPH", "company_brain")

db = FalkorDB(host=host, port=port)
graph = db.select_graph(graph_name)

result = graph.query("RETURN 1 AS result")

print("FalkorDB connection successful!")
print("Cypher result:", result.result_set)
