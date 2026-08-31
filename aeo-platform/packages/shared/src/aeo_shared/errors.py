from enum import IntEnum


class ErrorCode(IntEnum):
    """Unified error codes per docs/04_ARCHITECTURE_STANDARDS.md §5.3."""

    OK = 0

    # Client errors 10001-19999
    VALIDATION_ERROR = 10001
    UNAUTHORIZED = 10002
    RATE_LIMITED = 10003

    # Business errors 20001-29999
    TASK_NOT_FOUND = 20001
    TASK_INVALID_STATE = 20002
    TASK_QUEUE_FULL = 20030

    # Agent errors 20010-20019
    AGENT_TIMEOUT = 20010
    AGENT_FAILED = 20011
    TOKEN_LIMIT_EXCEEDED = 20012

    # HITL errors 20020-20029
    HITL_NOT_PENDING = 20020

    # System errors 50001-59999
    DATABASE_ERROR = 50001
    INTERNAL_ERROR = 50002
    SERVICE_UNAVAILABLE = 50003


ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.OK: "ok",
    ErrorCode.VALIDATION_ERROR: "validation error",
    ErrorCode.UNAUTHORIZED: "unauthorized",
    ErrorCode.RATE_LIMITED: "rate limit exceeded",
    ErrorCode.TASK_NOT_FOUND: "task not found",
    ErrorCode.TASK_INVALID_STATE: "task invalid state",
    ErrorCode.TASK_QUEUE_FULL: "task queue is full",
    ErrorCode.AGENT_TIMEOUT: "agent execution timeout",
    ErrorCode.AGENT_FAILED: "agent execution failed",
    ErrorCode.TOKEN_LIMIT_EXCEEDED: "token limit exceeded",
    ErrorCode.HITL_NOT_PENDING: "task is not pending human review",
    ErrorCode.DATABASE_ERROR: "database error",
    ErrorCode.INTERNAL_ERROR: "internal server error",
    ErrorCode.SERVICE_UNAVAILABLE: "service unavailable",
}
