
from app.tools.trace_decision import trace_decision


def test_postgres_decision():
    result = trace_decision("decision_postgres")

    assert result["found"] is True
    assert result["decision_id"] == "decision_postgres"

    technologies = [
        item["technology_name"]
        for item in result["chosen_technologies"]
    ]
    assert "PostgreSQL" in technologies

    affected = [
        item["entity_name"]
        for item in result["affected_entities"]
    ]
    assert "Transaction Service" in affected

    documents = [
        item["document_id"]
        for item in result["supporting_documents"]
    ]
    assert "doc_transaction_rfc" in documents


def test_unknown_decision():
    result = trace_decision("decision_does_not_exist")

    assert result["found"] is False


def test_blank_decision():
    result = trace_decision("   ")

    assert result["found"] is False

