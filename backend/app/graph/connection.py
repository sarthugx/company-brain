
import os
from pathlib import Path

from dotenv import load_dotenv
from falkordb import FalkorDB

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def create_db_connection():
    host = os.getenv("FALKORDB_HOST", "127.0.0.1")
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    graph_name = os.getenv("FALKORDB_GRAPH", "company_brain")
    protocol = int(os.getenv("FALKORDB_PROTOCOL", "2"))

    db = FalkorDB(host=host, port=port, protocol=protocol)
    graph = db.select_graph(graph_name)

    return db, graph
