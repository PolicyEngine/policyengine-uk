"""Small-cell rules for everything the report publishes.

The dataset is licensed survey microdata. A figure built from fewer than
``MIN_CELL`` records can reveal one of them: a benefit total and its
caseload from one recipient give the award and the survey weight. Such
figures are published as suppressed, and descriptions of fewer than
``MIN_CELL`` units give no count or weighted share.

Raw values of suppressed and rounded figures are kept under ``HIDDEN_KEY`` in
the household detail, which is written only to ``private/`` and never
uploaded. The comparison reads them there to publish a rounded total's exact
change when no suppressed head inside it changed, which reveals nothing the
published heads' changes don't.
"""

MIN_CELL = 10
SUPPRESSED = f"fewer than {MIN_CELL} records"
HIDDEN_KEY = "hidden"


def small(count: int) -> bool:
    """A non-empty cell too small to publish."""
    return 0 < count < MIN_CELL


def count_text(count: int, what: str) -> str:
    """``"N <what>"``, or ``"fewer than 10 <what>"`` for a small cell."""
    return f"fewer than {MIN_CELL} {what}" if small(count) else f"{count:,} {what}"
