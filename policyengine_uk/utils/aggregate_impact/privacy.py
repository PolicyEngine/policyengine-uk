"""Small-cell rules for everything the report publishes.

The dataset is licensed survey microdata. A figure built from fewer than
``MIN_CELL`` records can reveal one of them: a benefit total and its
caseload from one recipient give the award and the survey weight. Such
figures are published as suppressed, and descriptions of fewer than
``MIN_CELL`` units give no count or weighted share.

A total that contains a suppressed head or double count is rebuilt that year
from its other components (``measure.rebuild_protected``), and so are the
household incomes for deciles, so no published total includes it. Checks
whose verdict would depend on its values leave out the households holding it
(identities, the HBAI reproduction, overlap guards) or aren't run that year
(the sign check of the suppressed head). The tool withholds a reform's
costing and target change in a year they would come from a small cell
(``measure.reform_withheld``), and records which conditions withheld them
(``measure.withheld_reasons``): each reason names the condition and the
component or variable it holds for, never a count, an amount or a share. A
reason about a group the reform defines (a component's records under the
reform, or the households or records whose balance or target it changes)
says only that the group has "fewer than 10", as a decile row's "fewer than
10 households change" does.

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
- A withheld year's ``suppressed_component_changed`` reason says that the
  reform changes some record of a component the baseline suppresses, and
  names it: a yes or no that can turn on that component's few records, as
  the counted-once verdicts above do. The withheld figure already says that
  one of the conditions holds; the reason adds which, and which suppressed
  component, so a reader can tell a reform whose own change is too small to
  publish from one that only touches another small cell. A published year
  records no reason, so it says nothing new.
- A withheld year's ``small_target_change`` that names the reform's own
  target, beside the ``responsive:<id>`` verdict the report publishes for
  that year, says whether fewer than 10 records together moved the target by
  at least the reform's minimum: a bound on that cell's total, never its
  value. A ``small_balance_change`` says much the same when the target is
  part of gov_balance and nothing offsets it there. The counting rule above
  already publishes more (one household's £10,000 beside ten pennies).

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


# The conditions under which the tool withholds a reform's figures for a
# year (measure.withheld_reasons).
NO_BASELINE = "no_baseline"
SUPPRESSED_COMPONENT_CHANGED = "suppressed_component_changed"
SMALL_COMPONENT_LEFT = "small_component_left"
SMALL_BALANCE_CHANGE = "small_balance_change"
SMALL_TARGET_CHANGE = "small_target_change"
WITHHELD_CONDITIONS = (
    NO_BASELINE,
    SUPPRESSED_COMPONENT_CHANGED,
    SMALL_COMPONENT_LEFT,
    SMALL_BALANCE_CHANGE,
    SMALL_TARGET_CHANGE,
)


def withheld_reason(condition: str, variable=None, metric_id=None) -> dict:
    """One reason the tool withholds a reform year: the condition and what it
    holds for. ``metric_id`` is the published id of a partition component."""
    return {"condition": condition, "variable": variable, "metric_id": metric_id}


def withheld_text(reasons) -> str:
    """Reasons in words, with no count or amount: "fewer than 10" at most."""
    return "; ".join(_reason_text(reason) for reason in reasons)


def _reason_text(reason) -> str:
    condition = reason.get("condition")
    what = reason.get("metric_id") or reason.get("variable")
    if condition == NO_BASELINE:
        return "the baseline run recorded nothing for the year"
    if condition == SUPPRESSED_COMPONENT_CHANGED:
        return f"the reform changes a record of {what}, which the baseline suppresses"
    if condition == SMALL_COMPONENT_LEFT:
        return f"the reform leaves {what} with fewer than {MIN_CELL} records"
    if condition == SMALL_BALANCE_CHANGE:
        return f"the reform changes {what} in fewer than {MIN_CELL} households"
    if condition == SMALL_TARGET_CHANGE:
        return f"the reform changes {what} in fewer than {MIN_CELL} records"
    return f"unrecognised condition {condition}"
