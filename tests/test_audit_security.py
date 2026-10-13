import pytest
from agents.base import AuditTrail


def test_hmac_audit_verification_detects_tampering():
    audit = AuditTrail(secret_key="unit-test-unique-key")
    audit.log("tester", "test", "PASS", {"status": "safe"})
    audit.log("tester", "test", "PASS", {"status": "safe"})
    assert audit.verify_integrity()

    original = audit.logs[0]["event_type"]
    audit.logs[0]["event_type"] = "ALTERED"
    assert not audit.verify_integrity()
    audit.logs[0]["event_type"] = original

    original_hash = audit.logs[0]["current_hash"]
    audit.logs[0]["current_hash"] = "0" * 64
    assert not audit.verify_integrity()
    audit.logs[0]["current_hash"] = original_hash

    assert audit.verify_integrity()


def test_empty_audit_chain_is_valid():
    assert AuditTrail(secret_key="test-key").verify_integrity()
