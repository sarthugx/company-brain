
import pytest

from app.tools.blast_radius import blast_radius


def test_known_system():
    result = blast_radius("sys_payment_gateway")

    assert result["found"] is True
    assert result["target_system"]["system_name"] == "Payment Gateway"
    assert isinstance(result["affected_systems"], list)
    assert result["affected_count"] == len(result["affected_systems"])


def test_unknown_system():
    result = blast_radius("sys_does_not_exist")

    assert result["found"] is False
    assert result["affected_systems"] == []


def test_invalid_depth():
    with pytest.raises(ValueError):
        blast_radius("sys_payment_gateway", max_depth=10)
