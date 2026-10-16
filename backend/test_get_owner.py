
from app.tools.get_owner import get_owner


def test_payment_gateway_owner():
    result = get_owner("sys_payment_gateway")

    assert result["found"] is True
    assert result["system_name"] == "Payment Gateway"
    assert result["current_owner"]["owner"] == "Infrastructure & SRE"
    assert result["current_owner"]["valid_from"] == "2026-07-01"
    assert len(result["ownership_history"]) == 2


def test_unknown_system():
    result = get_owner("sys_does_not_exist")

    assert result["found"] is False
