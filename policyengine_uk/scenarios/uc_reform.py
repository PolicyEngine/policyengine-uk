from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.data.economic_assumptions import PROJECTION_END_YEAR
from policyengine_uk.utils.supplied_inputs import set_model_value
import numpy as np
import warnings
from policyengine_core.periods import instant


# Universal Credit Act 2025: the first tax year of the rebalancing (2026-27,
# ss. 2 to 4) and the last the s. 4 duty covers (2029-30).
FIRST_REBALANCING_YEAR = 2026
SECTION_4_LAST_YEAR = 2029
# The tax years in which the scenario sets the element: from the first year of
# the rebalancing to the end of the data's projection. Other code reads this
# (for example to warn that a reform to elements.disabled.amount does not reach
# these years' awards). Later years fall to the uc_LCWRA_element formula, which
# pays every claimant the new-claimant amount.
REBALANCING_YEARS = range(FIRST_REBALANCING_YEAR, PROJECTION_END_YEAR + 1)


# The standard allowance amounts the protected LCWRA amount is paired with in
# the Universal Credit Act 2025 s. 4(2) duty: every amount of the allowance.
STANDARD_ALLOWANCE_TYPES = (
    "SINGLE_YOUNG",
    "SINGLE_OLD",
    "COUPLE_YOUNG",
    "COUPLE_OLD",
)


def protected_lcwra_floor(
    previous_amount: float,
    previous_standard_allowances: dict,
    standard_allowances: dict,
    cpi_factor: float,
) -> float:
    """The lowest protected LCWRA amount the Universal Credit Act 2025 allows.

    s. 4(2): for each standard allowance amount, the protected LCWRA amount
    plus that allowance must be at least the previous tax year's sum,
    increased by the relevant CPI percentage (never below 0%, s. 4(4)(a)). s. 3
    switches off the element's ordinary uprating, so the amount otherwise stays
    where it was. All amounts are monthly.
    """
    factor = max(float(cpi_factor), 1.0)
    required = max(
        (previous_amount + previous_standard_allowances[claimant_type]) * factor
        - standard_allowances[claimant_type]
        for claimant_type in STANDARD_ALLOWANCE_TYPES
    )
    return max(float(previous_amount), required)


def _standard_allowances_monthly(sim: Microsimulation, year: int) -> dict:
    amounts = sim.tax_benefit_system.parameters(
        str(year)
    ).gov.dwp.universal_credit.standard_allowance.amount
    return {
        claimant_type: float(amounts[claimant_type])
        for claimant_type in STANDARD_ALLOWANCE_TYPES
    }


def _relevant_cpi_factor(sim: Microsimulation, year: int) -> float:
    """1 + the relevant CPI percentage for a tax year (UC Act 2025 s. 4(4)(a)):
    the CPI 12-month rate in the September before it. The 0% floor is applied
    in :func:`protected_lcwra_floor`."""
    inputs = sim.tax_benefit_system.parameters.gov.economic_assumptions.statutory_uprating_inputs
    return 1 + float(inputs.cpi_september(f"{year - 1}-09-01"))


# The date the fiscal-year annualisation samples a parameter at
# (policyengine_uk.utils.parameters).
FISCAL_YEAR_SAMPLE_DATE = "04-30"


def _protected_amount_parameter(sim: Microsimulation):
    return sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing.protected_health_element


def _protected_existing_health_element_monthly(
    sim: Microsimulation, year: int
) -> float:
    """The protected LCWRA amount for a tax year, monthly.

    UC Regs 2013 reg. 36 gives one amount to every pre-2026, severe conditions
    criteria or terminally ill claimant, whatever their age or couple status
    (£429.80 for 2026-27, SI 2026/113 reg. 3(3)(b)). Any non-null amount,
    legislated or set by a reform, is used as given. A tax year whose amount
    is null (not yet legislated):

    - to 2029-30 takes the s. 4 floor from the year before;
    - from 2030-31 takes the year before's amount uprated by the element's
      uprating index. The row stays in reg. 36 (s. 2 only relabels it), s. 4
      covers only 2026-27 to 2029-30, and s. 3 disapplies the SSAA 1992
      s. 150 up-rating only in the tax years ending 5 April 2026 to 5 April
      2029, so the review in 2029-30 governs the April 2030 rate again. The
      index is the one the new-claimant amount follows
      (``rebalancing/create_health_element_uprating.py``): the benefit
      uprating index, held in any year the freeze is in force, never falling.
    """
    parameter = _protected_amount_parameter(sim)
    amount = parameter(f"{year}-{FISCAL_YEAR_SAMPLE_DATE}")
    if amount is not None:
        return float(amount)
    first = min(
        int(entry.instant_str[:4])
        for entry in parameter.values_list
        if entry.value is not None
    )
    if year <= first:
        raise ValueError(
            f"No protected LCWRA amount is set for {year} or any earlier year."
        )
    previous = _protected_existing_health_element_monthly(sim, year - 1)
    if year > SECTION_4_LAST_YEAR:
        index = sim.tax_benefit_system.parameters.gov.economic_assumptions.indices.uc_health_element
        return previous * (
            index(f"{year}-{FISCAL_YEAR_SAMPLE_DATE}")
            / index(f"{year - 1}-{FISCAL_YEAR_SAMPLE_DATE}")
        )
    return protected_lcwra_floor(
        previous,
        _standard_allowances_monthly(sim, year - 1),
        _standard_allowances_monthly(sim, year),
        _relevant_cpi_factor(sim, year),
    )


NEW_CLAIMANT_STATUS = "uc_receives_new_claimant_health_element"
LCWRA_AMOUNT = "gov.dwp.universal_credit.elements.disabled.amount"


class UCHealthElementOverrideWarning(UserWarning):
    """An LCWRA amount reform is superseded by the rebalancing inputs."""


def warn_shadowed_lcwra_reform(sim) -> None:
    """Warn once when a reformed amount is read in an active rebalancing year.

    Statutory changes are sampled when annualising the LCWRA parameter;
    overrides of the built parameters are read at 1 January. Construction
    and Scenario.apply defer this check until all their changes have run,
    so a reform that also switches rebalancing off does not warn.
    """
    from policyengine_uk.utils.dated_reforms import legacy_override_bounds

    if getattr(sim, "_defer_uc_health_warning", False) or getattr(
        sim, "_uc_health_amount_warning_emitted", False
    ):
        return
    system = getattr(sim, "tax_benefit_system", None)
    if system is None:
        return
    assignments = [
        change
        for change in getattr(system, "dated_assignments", ())
        if change.path == LCWRA_AMOUNT
    ]
    override_windows = [
        legacy_override_bounds(change, system.parameters)
        for change in getattr(system, "legacy_overrides", ())
        if change.path == LCWRA_AMOUNT
    ]
    if not assignments and not override_windows:
        return
    rebalancing = system.parameters.gov.dwp.universal_credit.rebalancing
    years = []
    for year in REBALANCING_YEARS:
        if not rebalancing.active(year):
            continue
        statutory_sample = instant(f"{year}-{FISCAL_YEAR_SAMPLE_DATE}")
        annual_sample = instant(f"{year}-01-01")
        if any(
            change.start <= statutory_sample <= change.stop for change in assignments
        ) or any(start <= annual_sample <= stop for start, stop in override_windows):
            years.append(year)
    if years:
        warnings.warn(
            f"A reform to {LCWRA_AMOUNT} is superseded in "
            f"{', '.join(map(str, years))} by Universal Credit rebalancing inputs. "
            "For a health element reform in these years change "
            "gov.dwp.universal_credit.rebalancing.protected_health_element and "
            "gov.dwp.universal_credit.rebalancing.new_claimant_health_element.",
            UCHealthElementOverrideWarning,
            stacklevel=2,
        )
        sim._uc_health_amount_warning_emitted = True


def _new_claimant_health_element_status(
    sim: Microsimulation, year: int, drawn: np.ndarray, built_from_data: bool
) -> np.ndarray:
    """Which benefit units get the new-claimant LCWRA rate in a year.

    A value the situation or dataset supplies is used as given. Data without
    one takes the seeded draw, recorded as an input. A household situation
    without one gets the protected amount (the variable's default): a draw
    there would make a household's award depend on its position among the
    other benefit units in the simulation.
    """
    # sim.get_array reads the simulation's own branch (and the branches it
    # inherits from); the holder's get_array reads only the default branch.
    supplied = sim.get_array(NEW_CLAIMANT_STATUS, year)
    if supplied is not None:
        return np.asarray(supplied, dtype=bool)
    if built_from_data:
        status = np.asarray(drawn, dtype=bool)
    else:
        status = np.zeros(len(drawn), dtype=bool)
    sim.set_input(NEW_CLAIMANT_STATUS, year, status)
    return status


def add_universal_credit_reform(sim: Microsimulation):
    rebalancing = sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing

    generator = np.random.default_rng(43)

    uc_seed = generator.random(len(sim.calculate("benunit_id")))
    # rebalancing.new_claimant_share: WPI Economics' estimates for 2026-27 to
    # 2029-30, held after that (an assumption; see the parameter).
    new_claimant_share = rebalancing.new_claimant_share
    new_claimant_health_element = rebalancing.new_claimant_health_element
    is_data = built_from_data(sim)
    for year in REBALANCING_YEARS:
        if not rebalancing.active(year):
            continue
        is_post_2025_claimant = _new_claimant_health_element_status(
            sim, year, uc_seed < new_claimant_share(year), is_data
        )
        # Copy: calculate returns the simulation's cached array, and the writes
        # below must reach the cache only through set_input.
        current_health_element = np.array(sim.calculate("uc_LCWRA_element", year))
        has_health_element = current_health_element > 0
        # One protected amount for every pre-2026 claimant (reg. 36).
        current_health_element[has_health_element & ~is_post_2025_claimant] = (
            _protected_existing_health_element_monthly(sim, year) * 12
        )
        # New claimants: £217.26 a month from April 2026 (UC Act 2025 s. 2),
        # frozen to 2029-30 (s. 3) and uprated after.
        current_health_element[has_health_element & is_post_2025_claimant] = (
            new_claimant_health_element(year) * 12
        )  # Monthly amount * 12
        # Stored as an input, so that reforms keep it, but still the model's
        # own element unless one was entered (the benefit cap's LCWRA
        # exception reads entries differently).
        set_model_value(sim, "uc_LCWRA_element", year, current_health_element)

    # Standard allowance uplift is handled in the formula itself so user
    # reforms to the base amount are applied before the uplift.
    warn_shadowed_lcwra_reform(sim)


universal_credit_july_2025_reform = Scenario(
    simulation_modifier=add_universal_credit_reform,
)
