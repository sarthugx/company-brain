
from app.graph.connection import create_db_connection

_, graph = create_db_connection()

# Create a synthetic incident and its supporting document.
graph.query(
    """
    MERGE (i:Incident {id: 'incident_payment_timeout'})
    SET i.name = 'Payment Processing Timeout',
        i.description = 'Elevated payment timeouts affecting transaction processing.',
        i.severity = 'high',
        i.status = 'resolved',
        i.occurred_at = '2026-07-15'
    """
)

graph.query(
    """
    MERGE (d:Document {id: 'doc_payment_incident'})
    SET d.name = 'Payment Incident Postmortem',
        d.title = 'Payment Processing Incident Postmortem',
        d.description = 'Synthetic postmortem documenting impact and resolution.',
        d.content = 'A payment timeout incident affected the Payment Gateway and Transaction Service. The incident was resolved by the Infrastructure and SRE team.'
    """
)

# Connect the incident to existing systems.
graph.query(
    """
    MATCH (i:Incident {id: 'incident_payment_timeout'})
    MATCH (s:System {id: 'sys_payment_gateway'})
    MERGE (i)-[:AFFECTED]->(s)
    """
)

graph.query(
    """
    MATCH (i:Incident {id: 'incident_payment_timeout'})
    MATCH (s:System {id: 'sys_transaction_service'})
    MERGE (i)-[:AFFECTED]->(s)
    """
)

# Link the incident to a person already in the graph.
graph.query(
    """
    MATCH (p:Person {id: 'person_neha'})
    MATCH (i:Incident {id: 'incident_payment_timeout'})
    MERGE (p)-[:RESOLVED]->(i)
    """
)

# Connect the incident to its supporting document.
graph.query(
    """
    MATCH (d:Document {id: 'doc_payment_incident'})
    MATCH (i:Incident {id: 'incident_payment_timeout'})
    MERGE (d)-[:DESCRIBES]->(i)
    """
)

print("Incident data added successfully.")

result = graph.query(
    """
    MATCH (i:Incident {id: 'incident_payment_timeout'})
    OPTIONAL MATCH (i)-[:AFFECTED]->(s:System)
    RETURN i.name, i.severity, i.status, collect(s.name)
    """
)

for row in result.result_set:
    print("Incident:", row[0])
    print("Severity:", row[1])
    print("Status:", row[2])
    print("Affected systems:", row[3])
