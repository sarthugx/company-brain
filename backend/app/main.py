
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.tools.trace_decision import trace_decision
from app.tools.investigate_incident import investigate_incident
from app.tools.what_changed import what_changed
from pydantic import BaseModel, Field
from app.agent.agent import ask_company_brain

from app.graph.connection import create_db_connection
from app.tools.get_owner import get_owner
from app.tools.find_experts import find_experts
from app.tools.blast_radius import blast_radius

app = FastAPI(
    title="Company Brain API",
    description="Evidence-backed company intelligence powered by FalkorDB.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    try:
        _, graph = create_db_connection()
        result = graph.query("RETURN 1 AS result")

        if result.result_set != [[1]]:
            raise RuntimeError("Unexpected graph response")

        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Graph database is unavailable",
        ) from exc


@app.get("/api/owner/{system_id}")
def owner(system_id: str):
    return get_owner(system_id)


@app.get("/api/experts")
def experts(topic: str = Query(min_length=1, max_length=200)):
    return find_experts(topic)


@app.get("/api/blast-radius/{system_id}")
def system_blast_radius(
    system_id: str,
    max_depth: int = Query(default=5, ge=1, le=5),
):
    try:
        return blast_radius(system_id, max_depth=max_depth)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/decisions/{decision_id}")
def decision_trace(decision_id: str):
    return trace_decision(decision_id)

@app.get("/api/incidents/{incident_id}")
def incident_investigation(incident_id: str):
    return investigate_incident(incident_id)

@app.get("/api/changes")
def changes(
    start_date: str | None = None,
    end_date: str | None = None,
):
    try:
        return what_changed(start_date=start_date, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        return ask_company_brain(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Keep provider errors and internal details out of the public response.
        raise HTTPException(
            status_code=502,
            detail="The AI agent could not complete the request. Check backend logs.",
        ) from exc



@app.get("/api/graph")
def get_graph():
    try:
        _, graph = create_db_connection()

        result = graph.query(
            """
            MATCH (n)
            RETURN
                labels(n) AS labels,
                properties(n) AS properties
            """
        )

        nodes = []
        seen_ids = set()

        for row in result.result_set:
            labels, properties = row
            node_id = properties.get("id")

            if not node_id or node_id in seen_ids:
                continue

            seen_ids.add(node_id)

            nodes.append({
                "data": {
                    "id": str(node_id),
                    "label": str(
                        properties.get("name")
                        or properties.get("title")
                        or node_id
                    ),
                    "type": labels[0] if labels else "Unknown",
                    "properties": properties,
                }
            })

        relationship_result = graph.query(
            """
            MATCH (source)-[r]->(target)
            RETURN
                properties(source) AS source_properties,
                type(r) AS relationship,
                properties(target) AS target_properties
            """
        )

        edges = []

        for index, row in enumerate(relationship_result.result_set):
            source_properties, relationship, target_properties = row

            source_id = source_properties.get("id")
            target_id = target_properties.get("id")

            if not source_id or not target_id:
                continue

            edges.append({
                "data": {
                    "id": f"edge-{index}",
                    "source": str(source_id),
                    "target": str(target_id),
                    "label": relationship,
                }
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve the knowledge graph.",
        ) from exc
