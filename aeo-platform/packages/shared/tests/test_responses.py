from aeo_shared.errors import ERROR_MESSAGES, ErrorCode
from aeo_shared.responses import error_response, success_response


def test_error_codes_unique() -> None:
    codes = [int(c) for c in ErrorCode if c != ErrorCode.OK]
    assert len(codes) == len(set(codes))


def test_all_errors_have_messages() -> None:
    for code in ErrorCode:
        if code != ErrorCode.OK:
            assert code in ERROR_MESSAGES


def test_success_response() -> None:
    resp = success_response({"key": "value"}, "req-123")
    assert resp.code == 0
    assert resp.message == "ok"
    assert resp.data == {"key": "value"}
    assert resp.request_id == "req-123"


def test_error_response() -> None:
    resp = error_response(ErrorCode.TASK_NOT_FOUND, "req-456")
    assert resp.code == int(ErrorCode.TASK_NOT_FOUND)
    assert resp.data is None
    assert resp.request_id == "req-456"
