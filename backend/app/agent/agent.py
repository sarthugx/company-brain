
import json
import os
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI
from app.graph.connection import create_db_connection

from app.tools.get_owner import get_owner
from app.tools.find_experts import find_experts
from app.tools.blast_radius import blast_radius
from app.tools.trace_decision import trace_decision
from app.tools.investigate_incident import investigate_incident
from app.tools.what_changed import what_changed


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

SYSTEM_PROMPT = """
You are Company Brain, an evidence-grounded company intelligence assistant.

You answer questions about the synthetic company NovaTech using the supplied
graph tools. Use tools whenever the question asks for company-specific facts.

Rules:
- Never invent people, ownership, decisions, incidents, dates, or evidence.
- Base factual claims on tool results.
- Explain uncertainty and explicitly say when the graph has no supporting data.
- Distinguish evidence from inference.
- For decision rationale, do not infer why a technology was chosen from its name
  or a document title alone.
- Summarize relevant evidence and identify source document IDs when available.
- Do not claim a tool was executed unless it actually was.
- If a question is ambiguous, ask one concise clarification.
- Users may refer to systems, decisions, and incidents by their display names.
  The backend resolves exact entity names to canonical graph IDs.
- Call the appropriate tool once with the user's actual entity name or ID.
- If a tool returns found=false, do not repeatedly guess alternate spellings.
  Explain that no matching record was found, or ask for clarification.
- Do not make repeated calls with guessed IDs after a failed lookup.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_owner",
            "description": "Find the current owner and ownership history of a system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "System ID"}
                },
                "required": ["system_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_experts",
            "description": "Find people with graph evidence related to a project, incident, or document topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Project, incident, or document topic"}
                },
                "required": ["topic"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "blast_radius",
            "description": "Find downstream systems that may be affected if a system fails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string"},
                    "max_depth": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["system_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trace_decision",
            "description": "Trace a decision to its maker, chosen technology, affected entities, and supporting documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "decision_id": {"type": "string"}
                },
                "required": ["decision_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "investigate_incident",
            "description": "Investigate an incident, including affected systems, resolvers, and supporting documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"}
                },
                "required": ["incident_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "what_changed",
            "description": "Report recorded system ownership changes, optionally filtered by inclusive YYYY-MM-DD dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": ["string", "null"],
                        "description": "Inclusive start date in YYYY-MM-DD format, or null",
                    },
                    "end_date": {
                        "type": ["string", "null"],
                        "description": "Inclusive end date in YYYY-MM-DD format, or null",
                    },
                },
                "required": ["start_date", "end_date"],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "get_owner": get_owner,
    "find_experts": find_experts,
    "blast_radius": blast_radius,
    "trace_decision": trace_decision,
    "investigate_incident": investigate_incident,
    "what_changed": what_changed,
}


def _resolve_entity_id(label: str, supplied_value: str) -> str:
    """Resolve a graph entity's ID from either its ID or its exact name."""
    value = supplied_value.strip()
    if not value:
        return value

    _, graph = create_db_connection()

    result = graph.query(
        """
        MATCH (n)
        WHERE $label IN labels(n)
          AND (
            toLower(coalesce(n.id, '')) = toLower($value)
            OR toLower(coalesce(n.name, '')) = toLower($value)
          )
        RETURN n.id
        LIMIT 1
        """,
        {"label": label, "value": value},
    )

    if result.result_set and result.result_set[0][0]:
        return result.result_set[0][0]

    # Keep unknown values unchanged so the underlying tool returns
    # its normal not-found response.
    return value


def _run_tool(name: str, arguments: dict) -> dict:
    """Execute only a registered tool, with basic argument validation."""
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unsupported tool: {name}")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    allowed_arguments = {
        "get_owner": {"system_id"},
        "find_experts": {"topic"},
        "blast_radius": {"system_id", "max_depth"},
        "trace_decision": {"decision_id"},
        "investigate_incident": {"incident_id"},
        "what_changed": {"start_date", "end_date"},
    }[name]

    if set(arguments) - allowed_arguments:
        raise ValueError("Unexpected tool arguments.")

    if name == "blast_radius" and "max_depth" not in arguments:
        arguments["max_depth"] = 5

    if name == "what_changed":
        for field in ("start_date", "end_date"):
            value = arguments.get(field)
            if value is not None:
                try:
                    parsed = date.fromisoformat(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{field} must use YYYY-MM-DD format.") from exc
                if parsed.isoformat() != value:
                    raise ValueError(f"{field} must use YYYY-MM-DD format.")

    
    # Resolve human-readable names to canonical graph IDs.
    entity_arguments = {
        "get_owner": ("system_id", "System"),
        "blast_radius": ("system_id", "System"),
        "trace_decision": ("decision_id", "Decision"),
        "investigate_incident": ("incident_id", "Incident"),
    }

    if name in entity_arguments:
        argument_name, label = entity_arguments[name]
        supplied_value = arguments.get(argument_name)

        if isinstance(supplied_value, str):
            arguments[argument_name] = _resolve_entity_id(
                label, supplied_value
            )

    result = TOOL_FUNCTIONS[name](**arguments)

    return result


def ask_company_brain(question: str) -> dict:
    """Answer a natural-language question using controlled graph tool calls."""
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")
    if len(question) > 2000:
        raise ValueError("Question must be 2000 characters or fewer.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    tool_evidence = []
    max_rounds = 5

    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return {
                "answer": message.content or "I could not produce an answer from the available evidence.",
                "model": response.model,
                "evidence": tool_evidence,
            }

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = _run_tool(name, arguments)
                tool_output = {"ok": True, "result": result}
                tool_evidence.append({
                    "tool": name,
                    "arguments": arguments,
                    "result": result,
                })
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                tool_output = {"ok": False, "error": str(exc)}
            except Exception:
                # Do not expose internal connection strings, credentials, or traces.
                tool_output = {
                    "ok": False,
                    "error": "The graph tool failed. Try again or inspect backend logs.",
                }

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_output, default=str),
            })

    return {
        "answer": "I reached the tool-call limit before completing the investigation. Try a more specific question.",
        "model": MODEL,
        "evidence": tool_evidence,
    }
