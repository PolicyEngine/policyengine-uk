"""Small-cell rules for everything the report publishes.

The dataset is licensed survey microdata. A figure built from fewer than
``MIN_CELL`` records can reveal one of them: a benefit total and its
caseload from one recipient give the award and the survey weight. Such
figures are published as suppressed, and descriptions of fewer than
``MIN_CELL`` units give no count or weighted share.

A total that contains a suppressed head or double count is rebuilt that year
from its other components (``measure.rebuild_protected``), and so are the
household incomes for deciles, so no published total includes it. Parts of
HBAI income outside the partition that few records may hold
(``measure.HBAI_ONLY_COMPONENTS``) are counted and suppressed like heads, and
HBAI income leaves them out in the same way. Checks
whose verdict would depend on its values leave out the households holding it
(identities, the HBAI reproduction, overlap guards) or aren't run that year
(the sign check of the suppressed head). A reform's costing and target change
are withheld in a year they would come from a small cell
(``measure.reform_withheld``).

Deliberate exceptions:

- Other heads whose formulas read the suppressed figure (income tax on a
  taxable benefit, a means test) still respond to it, inside totals from 10
  or more records; exact changes between versions are published under the
  d1601 A ruling below.
- The counted-once and double-count-present verdicts for a component from
  fewer than 10 units depend on how other heads respond at those units. They
  are kept, as the only containment tests for that component; their counts,
  responses and coefficients are not published.
- Reform withholding counts households, not amounts: one household changing
  by £10,000 alongside ten changing by a penny is published. That is the same
  counting rule as for levels; no dominance rule is applied.

Threat model. The report defends against disclosure through any combination
of the figures it publishes, across any number of reports, from honest
changes to the model, the data or the reforms. It doesn't defend against the
author of a pull request in this repository: GitHub runs a ``pull_request``
workflow from the pull request's branch, so its author could read the data in
the job directly. A pull request from a fork can't: the job runs only for
branches of this repository (its ``if`` in ``aggregate-impact.yaml``), and
GitHub gives fork pull requests no secrets.

d1601 A (Max, 2026-10-17): publish exact changes between model versions (or
datasets), as policyengine-api does; level protection stays. A change in
fewer than 10 records of a national total with 10 or more is published
exactly. Decile rows and reform figures retain their small-change withholding.
"""

MIN_CELL = 10
SUPPRESSED = f"fewer than {MIN_CELL} records"


def small(count: int) -> bool:
    """A non-empty cell too small to publish."""
    return 0 < count < MIN_CELL


def count_text(count: int, what: str) -> str:
    """``"N <what>"``, or ``"fewer than 10 <what>"`` for a small cell."""
    return f"fewer than {MIN_CELL} {what}" if small(count) else f"{count:,} {what}"
