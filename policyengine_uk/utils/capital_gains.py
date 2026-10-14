"""Capital gains marginal tax rates against the baseline, and the realisation
response they drive."""

import warnings
import weakref
from dataclasses import dataclass
from typing import Mapping

import numpy as np

from policyengine_core import periods
from policyengine_core.simulations import Simulation

from policyengine_uk.utils.measurement_branches import measurement_branch
from policyengine_uk.utils.rule_comparison import same_rules


# The response, and the part of it on gains qualifying for Business Asset
# Disposal Relief, which capital_gains_tax reads to keep those gains apart.
RESPONSE_VARIABLES = (
    "capital_gains_behavioural_response",
    "capital_gains_badr_behavioural_response",
)

RESPONSE_SETTINGS = "gov.simulation.capital_gains_responses"
# The settings under RESPONSE_SETTINGS that select the response.
SETTINGS = (
    "elasticity",
    "mtr_elasticity",
    "separate_badr_elasticity",
    "badr_elasticity",
)

# Parameters that feed only behavioural responses, with their copies under
# the parameters' baseline. Every measurement neutralises the responses, so
# a reform to these alone cannot change a measured marginal rate.
RESPONSE_PARAMETERS = tuple(
    prefix + path
    for prefix in ("", "baseline.")
    for path in (
        RESPONSE_SETTINGS,
        "gov.simulation.labour_supply_responses",
        "gov.simulation.labor_supply_responses",
    )
)


def measure_mtr(
    simulation: Simulation,
    branch_name: str,
    period,
    gains: np.ndarray,
) -> np.ndarray:
    """Measure the capital gains MTR in a simulation, holding gains fixed.

    The measurement branch neutralises the behavioural responses and measures
    from inputs alone, so the rate is taken at ``gains`` and at earnings
    before any labour supply response, even where the simulation has already
    calculated gains after a response, or at gains of its own (see
    ``measurement_branch``).
    """
    branch = measurement_branch(
        simulation,
        branch_name,
        period,
        {"capital_gains_before_response": gains},
    )
    return branch.populations["person"]("marginal_tax_rate_on_capital_gains", period)


def rules_match_baseline(simulation: Simulation) -> bool:
    """Whether a simulation applies its baseline's rules.

    Settings that feed only behavioural responses are left out: the
    measurement neutralises the responses, so they cannot move a rate.
    """
    return same_rules(
        simulation.tax_benefit_system,
        simulation.baseline.tax_benefit_system,
        RESPONSE_PARAMETERS,
    )


def measure_capital_gains_mtrs(person, period) -> tuple[np.ndarray, np.ndarray]:
    """Return the reform and baseline capital gains MTRs for each person.

    Both rates are measured at the same level of gains, so the difference
    reflects the reform alone. Returns two zero arrays, measuring nothing,
    where the simulation has no baseline to compare against or applies its
    baseline's rules: the two rates would be equal, so the change is zero.
    That covers a simulation built without a reform (whose baseline is a
    copy of it), every branch of one, and a reform's own baseline; a
    simulation whose rules were changed after it was built is measured.

    Simulations hold their baseline as a separately constructed simulation
    rather than a branch, so the baseline rate has to be measured there. A
    branch of the reform simulation carries reform parameters, and reports no
    rate change however large the reform.
    """
    simulation: Simulation = person.simulation
    baseline = simulation.baseline
    if baseline is None or rules_match_baseline(simulation):
        zeros = np.zeros(person.count)
        return zeros, zeros
    baseline_count = baseline.populations["person"].count
    if baseline_count != person.count:
        raise ValueError(
            f"The simulation has {person.count} people and its baseline "
            f"{baseline_count}. The capital gains realisation response compares "
            "each person's marginal rate with the baseline's, so the baseline "
            "must hold the same people: subsample both, or set "
            f"{RESPONSE_SETTINGS}.elasticity to 0."
        )

    gains = person("capital_gains_before_response", period)
    reform_mtr = measure_mtr(simulation, "cgr_measurement", period, gains)
    baseline_mtr = measure_mtr(baseline, "baseline_cgr_measurement", period, gains)
    return reform_mtr, baseline_mtr


def badr_gains_before_response(person, period) -> np.ndarray:
    """Gains qualifying for Business Asset Disposal Relief before any response,
    up to the person's total gains. The lifetime limit is not applied: gains
    above it still qualify, and are charged at the main rates."""
    gains = person("capital_gains_before_response", period)
    return np.maximum(0, np.minimum(person("capital_gains_badr", period), gains))


class CapitalGainsResponseWarning(UserWarning):
    """An MTR elasticity applies alone, its period's retention-rate
    elasticities being at their defaults and so treated as zero."""


@dataclass(frozen=True)
class CapitalGainsResponseAssumption:
    """The realisation response a simulation applies in a period.

    ``convention`` is ``"retention"`` (gains scale by
    ``((1 - t1) / (1 - t0)) ** elasticity``), ``"mtr"`` (by
    ``(t1 / t0) ** mtr_elasticity``) or ``"static"`` (no response), where
    ``t0`` and ``t1`` are a person's baseline and reform marginal rates on
    gains. ``elasticity`` applies to gains other than those qualifying for
    Business Asset Disposal Relief, and ``badr_elasticity`` to those.
    ``sources`` says of each of those and of ``mtr_elasticity`` and
    ``separate_badr_elasticity`` whether it is current law (``"default"``),
    changed by the caller (``"override"``) or set to zero because an MTR
    elasticity applies alone (``"auto_resolved"``).
    """

    period: str
    convention: str
    elasticity: float
    badr_elasticity: float
    mtr_elasticity: float
    separate_badr_elasticity: bool
    sources: Mapping[str, str]
    mtr_auto_resolved: bool = False
    warnings: tuple = ()

    def to_dict(self) -> dict:
        """The assumption as JSON-serialisable values."""
        return {
            "period": self.period,
            "convention": self.convention,
            "elasticity": self.elasticity,
            "badr_elasticity": self.badr_elasticity,
            "mtr_elasticity": self.mtr_elasticity,
            "separate_badr_elasticity": self.separate_badr_elasticity,
            "sources": dict(self.sources),
            "mtr_auto_resolved": self.mtr_auto_resolved,
            "warnings": list(self.warnings),
        }


def resolve_capital_gains_responses(
    settings: Mapping, current_law: Mapping, period
) -> CapitalGainsResponseAssumption:
    """Resolve the response settings in force in a period.

    ``settings`` and ``current_law`` give each of :data:`SETTINGS` for the
    period, as set and under current law. A nonzero ``mtr_elasticity``
    selects the marginal tax rate convention, which takes no retention-rate
    elasticity. Retention-rate settings still at current law then count as
    zero for the period, and the assumption carries a warning; settings
    changed to a nonzero retention-rate elasticity raise. A setting changed
    to its current-law value can't be told apart from one left there, so it
    resolves the same way.
    """
    main = float(settings["elasticity"])
    mtr = float(settings["mtr_elasticity"])
    separate = bool(settings["separate_badr_elasticity"])
    badr = float(settings["badr_elasticity"]) if separate else main
    changed = {
        name: float(settings[name]) != float(current_law[name]) for name in SETTINGS
    }

    def source(name: str) -> str:
        return "override" if changed[name] else "default"

    sources = {
        "elasticity": source("elasticity"),
        "badr_elasticity": (
            "override"
            if changed["separate_badr_elasticity"] or changed["badr_elasticity"]
            else "default"
        )
        if separate
        else source("elasticity"),
        "mtr_elasticity": source("mtr_elasticity"),
        "separate_badr_elasticity": source("separate_badr_elasticity"),
    }
    period = str(period)
    if mtr == 0:
        return CapitalGainsResponseAssumption(
            period=period,
            convention="static" if main == 0 and badr == 0 else "retention",
            elasticity=main,
            badr_elasticity=badr,
            mtr_elasticity=0.0,
            separate_badr_elasticity=separate,
            sources=sources,
        )

    if main != 0 and changed["elasticity"]:
        raise ValueError(
            f"{RESPONSE_SETTINGS}.elasticity and "
            f"{RESPONSE_SETTINGS}.mtr_elasticity cannot both be nonzero for the "
            f"same period: in {period} the elasticity is {main:g} and "
            f"mtr_elasticity {mtr:g}. Set one of them to 0."
        )
    badr_inherited = not changed["separate_badr_elasticity"] and not (
        separate and changed["badr_elasticity"]
    )
    if badr != 0 and not badr_inherited:
        raise ValueError(
            f"{RESPONSE_SETTINGS}.badr_elasticity, in effect while "
            "separate_badr_elasticity is true, and "
            f"{RESPONSE_SETTINGS}.mtr_elasticity cannot both be nonzero for the "
            f"same period: in {period} the BADR elasticity is {badr:g} and "
            f"mtr_elasticity {mtr:g}. Set badr_elasticity to 0, "
            "separate_badr_elasticity to false, or mtr_elasticity to 0."
        )

    messages = ()
    if main != 0:
        sources["elasticity"] = "auto_resolved"
    if badr != 0:
        sources["badr_elasticity"] = "auto_resolved"
    auto_resolved = main != 0 or badr != 0
    if auto_resolved:
        messages = (
            f"{RESPONSE_SETTINGS}.mtr_elasticity is {mtr:g} in {period}, while "
            f"the retention-rate elasticity keeps its default of {main:g}. The "
            "two conventions can't be combined, so in that period the marginal "
            "tax rate convention applies alone and the retention-rate "
            f"elasticities count as 0. To keep this without the warning, set "
            f"{RESPONSE_SETTINGS}.elasticity to 0 for the same periods; to use "
            "the retention-rate default instead, set mtr_elasticity to 0. An "
            "MTR elasticity is not a restatement of a retention-rate one: -0.7 "
            "and 1.0 scale gains differently across a finite rate change.",
        )
    return CapitalGainsResponseAssumption(
        period=period,
        convention="mtr",
        elasticity=0.0,
        badr_elasticity=0.0,
        mtr_elasticity=mtr,
        separate_badr_elasticity=separate,
        sources=sources,
        mtr_auto_resolved=auto_resolved,
        warnings=messages,
    )


# The warnings each tax-benefit system has given, so a setting warns once per
# system and period however many simulations, branches and recalculations
# read it. Branches share their simulation's system.
_warned = weakref.WeakKeyDictionary()


def _resolve(simulation: Simulation, period, parameters):
    """Resolve the response settings in ``parameters`` (a simulation's own,
    as a formula receives them) against current law, warning where needed."""
    # The tax-benefit system module imports the variables, which import this
    # module.
    from policyengine_uk.tax_benefit_system import processed_parameters

    p = parameters(period).gov.simulation.capital_gains_responses
    current = processed_parameters().get_child(RESPONSE_SETTINGS)
    instant = periods.period(period).start
    settings = {name: getattr(p, name) for name in SETTINGS}
    assumption = resolve_capital_gains_responses(
        settings,
        {name: current.children[name](instant) for name in SETTINGS},
        period,
    )
    if assumption.warnings:
        key = (assumption.period, *(float(settings[name]) for name in SETTINGS))
        system = simulation.tax_benefit_system
        given = _warned.setdefault(system, set())
        if key not in given:
            given.add(key)
            for message in assumption.warnings:
                warnings.warn(message, CapitalGainsResponseWarning, stacklevel=2)
    return assumption


def capital_gains_response_assumption(
    simulation: Simulation, period
) -> CapitalGainsResponseAssumption:
    """The realisation response ``simulation`` applies in ``period``.

    Resolved as the response itself resolves it, from the simulation's own
    parameters, after every reform and modifier applied so far: it raises on
    settings that conflict, and warns once where an MTR elasticity applies
    alone. ``to_dict()`` gives the assumption to record with a run's results.
    """
    period = periods.period(period)
    return _resolve(
        simulation, period, simulation.tax_benefit_system.get_parameters_at_instant
    )


def realisation_factors(person, period, parameters):
    """Factors by which realised gains scale under a reform, as (main, BADR).

    Gains qualifying for Business Asset Disposal Relief take
    capital_gains_badr_elasticity and the rest of the person's gains take
    capital_gains_elasticity. Both respond to the same share-weighted change
    in the person's marginal rate, so the elasticity is the only difference.
    The marginal tax rate convention has one elasticity for all gains.

    Returns None where there is no response: no baseline to compare against,
    no elasticity in force (see capital_gains_response_assumption), or no
    person with gains or losses to respond.
    """
    assumption = _resolve(person.simulation, period, parameters)
    if person.simulation.baseline is None or assumption.convention == "static":
        return None
    if not np.any(person("capital_gains_before_response", period) != 0):
        return None

    if assumption.convention == "mtr":
        change = person("relative_capital_gains_mtr_change", period)
        factor = np.exp(assumption.mtr_elasticity * change)
        return factor, factor

    change = person("relative_capital_gains_retention_rate_change", period)
    main = np.exp(person("capital_gains_elasticity", period) * change)
    badr = np.exp(person("capital_gains_badr_elasticity", period) * change)
    return main, badr


def held_realisation_responses(person, period) -> dict:
    """The realisation responses a simulation calculated, to hold fixed in a
    branch that steps one of its inputs to measure a marginal rate.

    A response measured again in such a branch would compare a rate at the
    stepped input with the baseline's at the original one, and count the
    step as a reform. Responses neutralised in the simulation (as in a
    measurement branch) are not held.
    """
    variables = person.simulation.tax_benefit_system.variables
    return {
        response: person(response, period)
        for response in RESPONSE_VARIABLES
        if not variables[response].is_neutralized
    }


def hold_realisation_responses(branch: Simulation, period, held: dict) -> None:
    """Set the responses :func:`held_realisation_responses` returned on a
    branch, so the branch reads them instead of measuring them again."""
    for response, values in held.items():
        branch.set_input(response, period, values)
