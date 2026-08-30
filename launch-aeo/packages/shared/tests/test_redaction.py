from aeo_shared.redaction import REDACTED, is_sensitive_key, redact_value


def test_redact_sensitive_top_level_keys() -> None:
    payload = {
        "api_key": "secret-key",
        "password": "hunter2",
        "supplier_price": 12.5,
        "cost_price": 8.0,
        "sku": "X431",
    }
    result = redact_value(payload)
    assert result["api_key"] == REDACTED
    assert result["password"] == REDACTED
    assert result["supplier_price"] == REDACTED
    assert result["cost_price"] == REDACTED
    assert result["sku"] == "X431"


def test_redact_sensitive_nested_keys() -> None:
    payload = {"product_info": {"supplier_price": 99.0, "name": "tool"}}
    result = redact_value(payload)
    assert result["product_info"]["supplier_price"] == REDACTED
    assert result["product_info"]["name"] == "tool"


def test_redact_case_insensitive_keys() -> None:
    payload = {"API_KEY": "secret", "Password": "x"}
    result = redact_value(payload)
    assert result["API_KEY"] == REDACTED
    assert result["Password"] == REDACTED


def test_is_sensitive_key() -> None:
    assert is_sensitive_key("api_key")
    assert is_sensitive_key("SUPPLIER_PRICE")
    assert not is_sensitive_key("sku")
