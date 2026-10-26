import datetime
from typing import NamedTuple

from policyengine_core.model_api import *
from policyengine_core import periods

from policyengine_uk.utils.ni_parameter_scales import (
    add_ni_scale_compatibility,
    canonicalize_ni_parameter_path,
    canonical_descendants,
)

from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
    canonicalize_lsr_parameter_path,
)


def str_to_instant(s):
    return periods.Instant(tuple(map(lambda s: int(s), s.split("-"))))


# Parameter metadata a dated reform records (``write_assignment``) when its
# change starts on or before the parameter's first stated value: that value,
# which backdating then extends instead of the change's. Recording it rather
# than writing it at the backdating date keeps the generation steps, which run
# before backdating and read a parameter's first year, seeing the parameter as
# current law does.
BACKDATED_VALUE = "backdated_value"


def backdate_parameters(root: str = None, first_instant: str = "2021-01-01") -> Reform:
    first_instant = str_to_instant(first_instant)
    node = root
    for param in canonical_descendants(node):
        if isinstance(param, Parameter):
            earliest = param.values_list[-1]
            earliest_value = earliest.value
            if param.metadata and BACKDATED_VALUE in param.metadata:
                earliest_value = param.metadata.pop(BACKDATED_VALUE)
            earliest_instant = str_to_instant(earliest.instant_str)
            if first_instant < earliest_instant:
                num_days = (earliest_instant.date - first_instant.date).days
                param.update(
                    period=periods.Period(("day", first_instant, num_days)),
                    value=earliest_value,
                )
    return root


def fiscal_year_average(param, year: int):
    """Day-weighted average of a parameter across a UK fiscal year.

    Returns None where any value in the year is missing or non-numeric, so
    the caller can fall back to sampling a single date.
    """
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)

    changes = []
    for value_at_instant in param.values_list:
        try:
            instant = datetime.date.fromisoformat(value_at_instant.instant_str)
        except ValueError:
            return None
        if start < instant < end:
            changes.append(instant)

    boundaries = [start, *sorted(changes), end]
    total = 0.0
    for segment_start, segment_end in zip(boundaries, boundaries[1:]):
        value = param(segment_start.isoformat())
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        total += value * (segment_end - segment_start).days

    return total / (end - start).days


def uk_fiscal_year_period(time_period):
    """Translate a bare year into the UK fiscal year it names.

    A UK parameter change for "2025" means the fiscal year starting 6 April
    2025. Writing it as the calendar year leaves January to April of 2026
    on prior law, which fiscal-year conversion then blends into the value —
    an annual override of 0.5 came out as 0.42. Non-year periods pass
    through untouched.
    """
    year = None
    if isinstance(time_period, int):
        year = time_period
    elif isinstance(time_period, str) and time_period.strip().isdigit():
        year = int(time_period.strip())
    if year is None or not 1900 < year < 2200:
        return time_period
    start = periods.Instant((year, 4, 6))
    days = (datetime.date(year + 1, 4, 6) - datetime.date(year, 4, 6)).days
    return periods.Period(("day", start, days))


def _fiscal_year_conversion_years(param):
    """Finite annual steps needed by this leaf's stated timeline.

    Keep the 26 legacy annual records and the first following boundary. A
    stated change then adds the annual labels it can affect, without filling
    an arbitrary projection horizon. Raw keys before 2015, including year 0000,
    remain opaque and are retained by Parameter.update.
    """
    years = set(range(2015, 2042))
    blend = (param.metadata or {}).get("fiscal_year_blend", False)
    for point in param.values_list:
        year = int(point.instant_str[:4])
        if year < 2015:
            continue
        month_day = point.instant_str[5:]
        if blend:
            fiscal_year = year if month_day >= "04-06" else year - 1
            years.update((fiscal_year, fiscal_year + 1))
        else:
            years.add(year if month_day <= "04-30" else year + 1)
    last_representable = 9998 if blend else 9999
    if max(years) > last_representable:
        raise ValueError(
            f"Cannot annualise {param.name}: its fiscal conversion needs a "
            "date beyond the supported Gregorian year 9999"
        )
    return sorted(year for year in years if year >= 2015)


def convert_to_fiscal_year_parameters(parameters):
    """Give each calendar-labelled year its UK fiscal parameter value.

    Ordinary leaves take their 30 April value. Opt-in ``fiscal_year_blend``
    leaves retain the existing day-weighted average from 6 April to 5 April
    and its single-date fallback. ``preserve_calendar_dates`` leaves are untouched.

    Sampling a single date drops any change taking effect later in the fiscal
    year. Parameters carrying `fiscal_year_blend: true` in their metadata are
    day-weighted across the year instead, which is the right annualisation for
    a rate or threshold that applies to a flow spread over the year. Leave the
    flag off where the value at a point in time is what applies, as for a tax
    charged on a transaction at the rate in force on its date.

    Ordinary Parameter histories retain all 2015–2040 annual records, an
    explicit 2041 boundary and finite later steps induced by stated changes.
    Dates within a calendar label therefore read the same annual value even
    beyond 2040. This annualises known values; it does not project new values.

    Domain checks and snapshot sampling finish before any live write.
    Start-only writes remove intervening raw dates and retain the original
    entries before 2015.
    """
    planned = []
    for param in canonical_descendants(parameters):
        if not isinstance(param, Parameter):
            continue
        if (param.metadata or {}).get("preserve_calendar_dates", False):
            continue
        planned.append((param, _fiscal_year_conversion_years(param)))

    # No live Parameter, list or root cache is changed during preflight or
    # snapshot sampling. In particular a late invalid leaf cannot follow an
    # already-rewritten earlier one.
    sampled = []
    for param, years in planned:
        snapshot = param.clone()
        blend = (snapshot.metadata or {}).get("fiscal_year_blend", False)
        values = []
        for year in years:
            value = fiscal_year_average(snapshot, year) if blend else None
            if value is None:
                value = snapshot(f"{year}-04-30")
            values.append((year, value))
        sampled.append((param, values))

    for param, values in sampled:
        for year, value in values:
            param.update(start=f"{year}-01-01", value=value)
    return parameters


_STATE_PENSION_AGE_REPLACEMENT = (
    "State Pension age now follows the statutory timetable by date of birth "
    "(Pensions Act 1995 Sch 4 para 1). Change the rows of "
    "gov.dwp.state_pension.age.age_by_birth_date (the age, in months) or "
    "gov.dwp.state_pension.age.day_by_birth_date (the day) for the births you "
    "want to change, for example gov.dwp.state_pension.age.age_by_birth_date[14]"
    ".amount for people born from 6 March 1961 until the next bracket, or "
    "gov.dwp.state_pension.age.male.age for men born before 6 December 1953. "
    "Read a person's State Pension age from the state_pension_age or is_SP_age "
    "variables."
)

_OBR_ELASTICITIES_REPLACEMENT = (
    "Nothing read it, so setting it never changed any output. The OBR's labour "
    "supply elasticities are applied by Simulation.apply_dynamics, called on a "
    "simulation with a baseline, when gov.dynamic.obr_labour_supply_assumptions "
    "is true, which it is by default."
)


class RemovedParameter(NamedTuple):
    label: str
    replacement: str


# Parameters removed from the tree, with the label of the node left at each
# path and what replaces the parameter, so a reform or saved policy that still
# names one fails with directions instead of a bare lookup error.
REMOVED_PARAMETERS = {
    "gov.dwp.state_pension.age.male": RemovedParameter(
        "removed male State Pension age parameter", _STATE_PENSION_AGE_REPLACEMENT
    ),
    "gov.dwp.state_pension.age.female": RemovedParameter(
        "removed female State Pension age parameter", _STATE_PENSION_AGE_REPLACEMENT
    ),
    "gov.dwp.carer_premium.couple": RemovedParameter(
        "removed couple carer premium parameter",
        "The carer premium is calculated per qualifying claimant or partner. "
        "Change gov.dwp.carer_premium.single (the per-person weekly amount) instead.",
    ),
    "gov.simulation.labour_supply_responses.obr_elasticities": RemovedParameter(
        "removed OBR elasticities switch", _OBR_ELASTICITIES_REPLACEMENT
    ),
    "gov.dwp.pension_credit.income.savings_credit_excluded_sources": RemovedParameter(
        "removed duplicate Savings Credit excluded-income list",
        "The model never read it. Change "
        "gov.dwp.pension_credit.savings_credit.excluded_income, the list of "
        "income that is not qualifying income for Savings Credit (SPC Regs "
        "2002 reg 9), instead.",
    ),
    "gov.dft.bus.reference_year": RemovedParameter(
        "removed bus fare reference year",
        "Bus fares now follow gov.dft.bus.local_bus_fares_index from the "
        "benchmark year gov.dft.bus.benchmark_year, and the cap term compares "
        "gov.dft.bus.fares.cap with gov.dft.bus.reference_fares.cap in the same "
        "year. Change gov.dft.bus.fares.cap to model a cap.",
    ),
    "gov.dft.bus.uncapped_single_fare": RemovedParameter(
        "removed single uncapped bus fare",
        "Cap changes are priced from a table of uncapped single fares, "
        "gov.dft.bus.uncapped_single_fares, with the share of single tickets "
        "and the mean fare of each band (LOW, MIDDLE, HIGH). To price every "
        "single ticket at one fare, set that band's share to 1 and the others "
        "to 0, or supply local_bus_uncapped_single_fare for each person.",
    ),
}


def check_parameter_not_removed(path: str) -> None:
    """Raise a ValueError naming the replacement if path was removed.

    A legacy ``labor_supply_responses`` path is checked as its
    ``labour_supply_responses`` equivalent.
    """
    removed = REMOVED_PARAMETERS.get(canonicalize_lsr_parameter_path(path))
    if removed is not None:
        raise ValueError(
            f"The parameter {path} has been removed. {removed.replacement}"
        )


class RemovedParameterNode(ParameterNode):
    """Keep a removed path discoverable without accepting scalar reforms.

    Male State Pension age still has valid children, so the compatibility
    node must support normal tree traversal and cloning. API reform code
    reads values_list before updating; both operations give migration help.
    Read at an instant, the node is an empty node rather than an error, so
    that its parent can still be read at an instant.
    """

    @property
    def values_list(self):
        check_parameter_not_removed(self.name)

    def update(self, *args, **kwargs):
        check_parameter_not_removed(self.name)


class RemovedParameterRoot(ParameterNode):
    """Reject explicit lookups of removed scalars, including empty policies."""

    def get_child(self, path: str):
        check_parameter_not_removed(path)
        return super().get_child(canonicalize_ni_parameter_path(path))


def add_removed_parameter_aliases(parameters: ParameterNode) -> ParameterNode:
    if not isinstance(parameters, RemovedParameterRoot):
        root = RemovedParameterRoot(parameters.name, data={})
        root.__dict__ = parameters.__dict__.copy()
        for child in root.children.values():
            child.parent = root
        parameters = root
    for path, removed in REMOVED_PARAMETERS.items():
        parent_path, name = path.rsplit(".", 1)
        parent = parameters
        for part in parent_path.split("."):
            parent = parent.children[part]
        previous = parent.children.get(name)
        if isinstance(previous, RemovedParameterNode):
            continue
        if previous is not None and not isinstance(previous, ParameterNode):
            raise ValueError(
                f"{path} is listed in REMOVED_PARAMETERS but the parameter still "
                "exists. Delete its YAML file, or remove it from REMOVED_PARAMETERS."
            )
        alias = RemovedParameterNode(path, data={})
        if previous is not None:
            alias.metadata.update(previous.metadata)
            for child_name, child in previous.children.items():
                alias.add_child(child_name, child)
        alias.description = (
            f"The parameter {path} has been removed. {removed.replacement}"
        )
        alias.metadata.update(
            label=removed.label,
            removed=True,
            economy=False,
            household=False,
        )
        parent.children[name] = alias
        setattr(parent, name, alias)
        alias.parent = parent
    return add_ni_scale_compatibility(parameters)
