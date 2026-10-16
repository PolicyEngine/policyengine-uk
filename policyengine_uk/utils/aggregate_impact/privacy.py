"""Small-cell rules for everything the report publishes.

The dataset is licensed survey microdata. A figure built from fewer than
``MIN_CELL`` records can reveal one of them: a benefit total and its
caseload from one recipient give the award and the survey weight. Such
figures are published as suppressed, and descriptions of fewer than
``MIN_CELL`` units give no count or weighted share.

A total that contains a suppressed head or double count is rebuilt that year
from its other components (``measure.rebuild_protected``), and so are the
household incomes for deciles, so no published figure depends on the
suppressed one's values. A reform's costing and target change are withheld in
a year they would come from a small cell (``measure.reform_withheld``).

Threat model. The report defends against disclosure through any combination
of the figures it publishes, across any number of reports, from honest
changes to the model, the data or the reforms. It doesn't defend against the
author of a pull request in this repository: GitHub runs a ``pull_request``
workflow from the pull request's branch, so its author could read the data in
the job directly. A pull request from a fork can't: the job runs only for
branches of this repository (its ``if`` in ``aggregate-impact.yaml``), and
GitHub gives fork pull requests no secrets.

Still open, for d1601: exact changes between two model versions (or two
datasets) are published, and a change in fewer than 10 records of a total
with 10 or more is that change alone. Decile rows and reform figures withhold
those; national totals don't yet.
"""

MIN_CELL = 10
SUPPRESSED = f"fewer than {MIN_CELL} records"


def small(count: int) -> bool:
    """A non-empty cell too small to publish."""
    return 0 < count < MIN_CELL


def count_text(count: int, what: str) -> str:
    """``"N <what>"``, or ``"fewer than 10 <what>"`` for a small cell."""
    return f"fewer than {MIN_CELL} {what}" if small(count) else f"{count:,} {what}"
