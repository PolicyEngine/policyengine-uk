"""Project the State Pension weekly rates year by year, rounded as DWP rounds.

Each April's Up-rating Order raises the full rate of the new State Pension and
the basic State Pension from the previous year's published weekly rate and
rounds the result. Social Security Administration Act 1992 s.150A(4) leaves
the rounding to the Secretary of State ("up or down to such extent as he
thinks appropriate"). DWP applies the review's percentage "to the current
full weekly rates of the basic and new State Pensions. The resulting amounts
are rounded to the nearest 5p" (written answer HL10770, 20 October 2025), and
HM Treasury's forecast baseline projects both rates "rounded to the nearest
5p" (Budget 2026 policy costings, Annex A). The previous year's rate,
uprated and rounded to the nearest 5p, gives every published basic rate from
April 2011 and every full new rate from April 2017
(``tests/test_triple_lock_outturn.py``). Rounding always up or always down to
5p, or to the nearest 10p, misses at least five of those years each.

A partial award rises by the same percentage as the rounded full rate
(HL10770: the rounding "results in a percentage rate which is applied to
each individual's existing pension payment"), which is what
``new_state_pension`` and ``basic_state_pension`` already pay: a share of
the full rate.

General uprating would instead multiply the last stated rate by its index's
growth since then, unrounded: £250.711 for April 2027, where HM Treasury's
Pension Tax Allowance explainer gives the full new State Pension for 2027-28
as £13,036.40, 52 weeks at £250.70. Rounding that path would not be enough,
because the Order rounds each year from the last published, already rounded,
rate: £250.70 x 1.034 = £259.2238 gives £259.20 for April 2028, where the
unrounded path, £259.2357, would round to £259.25.

So for each rate this step fills the years after its last stated value,
through the last year of its uprating index, with the previous year's rate
times the index's growth over the year, to the nearest multiple of
``gov.dwp.state_pension.weekly_rate_rounding``. No published rate has
landed exactly on a half, so the sources do not say which way a half goes;
this step rounds halves up. Each value applies from 1 January, as
uprating's do, so the April uprating sets the fiscal year,
and general uprating then has no year left to fill. The growth comes from
the index named in the rate's ``uprating`` metadata, so a reform to the
triple lock rate, its inputs or the index moves the projection. The product
is taken to 0.0001p before rounding, which drops float noise without moving
a value the inputs state exactly (a rate on the 5p grid times a rise in
tenths of a percentage point has at most five decimal places).

Runs as a generation step, after the economic assumption indices: the
baseline copy, prior law's projected path for dated reforms and the
fiscal-year annualisation all see the rounded rates.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant

from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    uprating_instant,
)

PROJECTED_RATES = ("new_state_pension", "basic_state_pension")
# Drops float noise in the uprated amount (well under 1e-9 of a pound) and
# keeps every digit an exact product of the inputs has.
PRODUCT_PRECISION = Decimal("0.000001")


def _decimal(value: float) -> Decimal:
    return Decimal(repr(float(value)))


def round_weekly_rate(amount: Decimal, unit: Optional[float]) -> float:
    """``amount`` to the nearest multiple of ``unit``, halves up.

    A zero or missing unit leaves the amount unrounded.
    """
    amount = amount.quantize(PRODUCT_PRECISION, ROUND_HALF_UP)
    if not unit:
        return float(amount)
    step = _decimal(unit)
    return float((amount / step).quantize(Decimal(1), ROUND_HALF_UP) * step)


def uprate_weekly_rate(
    previous: float, growth: Decimal, unit: Optional[float]
) -> float:
    """The previous year's rate raised by ``growth`` (a ratio), then rounded."""
    return round_weekly_rate(_decimal(previous) * growth, unit)


def uprating_index(parameters: ParameterNode, rate: Parameter) -> Parameter:
    """The index named in the rate's ``uprating`` metadata."""
    meta = rate.metadata["uprating"]
    name = meta["parameter"] if isinstance(meta, dict) else meta
    return parameters.get_child(name)


def project_weekly_rate(rate: Parameter, index: Parameter, rounding: Parameter) -> None:
    """Fill the years after the rate's last stated value, through the index's
    last year, each from the year before."""
    last = max(rate.values_list, key=lambda entry: entry.instant_str)
    value = last.value
    level = index(last.instant_str)
    if value is None or level is None:
        return
    for entry in sorted(index.values_list, key=lambda entry: entry.instant_str):
        if entry.instant_str <= last.instant_str:
            continue
        new_level = index(entry.instant_str)
        unit = rounding(uprating_instant(int(entry.instant_str[:4])))
        value = uprate_weekly_rate(value, _decimal(new_level) / _decimal(level), unit)
        rate.values_list.append(
            ParameterAtInstant(rate.name, entry.instant_str, data=value)
        )
        level = new_level
    rate.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    rate.mark_as_modified()


def project_state_pension_rates(parameters: ParameterNode) -> ParameterNode:
    """Project the full new and basic State Pension weekly rates."""
    state_pension = parameters.gov.dwp.state_pension
    for scheme in PROJECTED_RATES:
        rate = state_pension.get_child(f"{scheme}.amount")
        project_weekly_rate(
            rate,
            uprating_index(parameters, rate),
            state_pension.weekly_rate_rounding,
        )
    state_pension.clear_parent_cache()
    return parameters
