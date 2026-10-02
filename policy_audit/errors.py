"""Exceptions raised by the policy audit tool."""


class PolicyAuditError(Exception):
    """Base error for deterministic policy-audit failures."""


class ReviewValidationError(PolicyAuditError):
    """Raised when a structured audit review is incomplete or inconsistent."""
