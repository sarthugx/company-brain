
from app.tools.investigate_incident import investigate_incident


def test_payment_timeout_incident():
    result = investigate_incident("incident_payment_timeout")

    assert result["found"] is True
    assert result["incident"]["severity"] == "high"
    assert result["incident"]["status"] == "resolved"

    systems = {
        item["system_name"]
        for item in result["affected_systems"]
    }
    assert "Payment Gateway" in systems
    assert "Transaction Service" in systems

    resolvers = {
        item["person_name"]
        for item in result["resolvers"]
    }
    assert "Neha Kulkarni" in resolvers

    documents = {
        item["document_id"]
        for item in result["supporting_documents"]
    }
    assert "doc_payment_incident" in documents


def test_unknown_incident():
    result = investigate_incident("incident_does_not_exist")
    assert result["found"] is False


def test_blank_incident():
    result = investigate_incident("   ")
    assert result["found"] is False
