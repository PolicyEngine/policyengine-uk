from policyengine_uk.model_api import *
from policyengine_core.parameters import ParameterNode
from policyengine_uk.utils.excise import fiscal_year_segments
from policyengine_uk.utils.supplied_inputs import stored_as_input


def hb_uses_annual_override(benunit, period, variable_name, default_formula):
    """Keep annual inputs, replacement formulas and computed aggregates out of
    recalculation. A defined_for mask on the model's formula is none of
    these: the segment helpers apply it themselves (hb_apply_defined_for)."""
    variable = benunit.simulation.tax_benefit_system.get_variable(variable_name)
    formula = variable.get_formula(period)
    if formula is None or formula.__code__ != default_formula.__code__:
        return True
    return hb_reads_no_other_variable(benunit, period, variable_name)


def hb_apply_defined_for(benunit, period, variable_name, amount):
    """The amount a segment helper rebuilt for the variable where the
    variable's defined_for condition holds, and the variable's default
    elsewhere. Core masks the annual output the same way
    (Simulation._calculate): it maps the condition to the variable's entity
    and keeps the amount where the condition exceeds zero. The condition
    comes from the variable the simulation holds, so one that a reform adds
    reaches each segment, as it reaches the annual output."""
    variable = benunit.simulation.tax_benefit_system.get_variable(variable_name)
    if variable.defined_for is None:
        return amount
    condition = benunit.simulation.calculate(
        variable.defined_for, period, map_to=variable.entity.key
    )
    return where(np.asarray(condition) > 0, amount, variable.default_value)


def hb_can_read_other_variables(variable, period):
    """Whether core, reading the variable for a period it holds no value
    for, can read another variable. It first calculates any ``defined_for``
    mask, then runs the formula for the period or, without one, computes
    ``adds`` and ``subtracts``, each a list of variable and parameter names
    or the path of a parameter that lists them. Otherwise it uprates or
    carries over the variable's own earlier inputs, or returns its
    default."""
    return bool(
        variable.defined_for is not None
        or variable.get_formula(period) is not None
        or variable.adds
        or variable.subtracts
    )


def hb_reads_no_other_variable(benunit, period, variable_name):
    """Whether reading the variable for this period reads no other variable:
    a reform neutralized it, or left it with no formula, aggregate or
    ``defined_for`` mask, or an input supplies it."""
    variable = benunit.simulation.tax_benefit_system.get_variable(variable_name)
    if variable.is_neutralized or not hb_can_read_other_variables(variable, period):
        return True
    # An input the caller set for this period overrides recalculation, and so
    # does a scenario's own value (set_model_value), which the variable then
    # reads; a cached formula result does not, even in populations taken from
    # another simulation or in their clones and branches.
    # SUPPLIED_INPUT_VARIABLES lists each name passed here, as stored_as_input
    # and set_model_value require.
    return stored_as_input(benunit, variable_name, period)


def hb_accommodation_segments(benunit, period, parameters):
    """Full annual-equivalent accommodation amounts and fiscal-year weights.
    Each amount is nil where the disregard's defined_for condition fails."""
    name = "housing_benefit_specified_or_temporary_accommodation_disregard"
    if hb_uses_annual_override(
        benunit,
        period,
        name,
        housing_benefit_specified_or_temporary_accommodation_disregard.formula,
    ):
        yield benunit(name, period), 1
        return
    raw = benunit.simulation.tax_benefit_system.parameters
    accommodation = raw.gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation
    schedule = ParameterNode("hb_accommodation_schedule", data={})
    for family in ("single", "lone_parent", "couple"):
        for age, leaf in accommodation.children[family].children.items():
            # add_child sets the parent: clone leaves, never modify the model
            # tree or replace values supplied by a parameter reform.
            schedule.add_child(f"{family}_{age}", leaf.clone())
    p = parameters(
        period
    ).gov.dwp.housing_benefit.means_test.income_disregard.specified_or_temporary_accommodation
    person = benunit.members
    earner = (
        (person("employment_income", period) > 0)
        | (person("self_employment_income", period) != 0)
        | (person("employment_benefits", period) > 0)
    )
    has_earner = benunit.any(person("is_claimant_or_partner", period) & earner)
    eldest = benunit("eldest_claimant_or_partner_age", period)
    older = eldest >= p.age_threshold.older
    applies = (
        benunit("in_specified_or_temporary_accommodation", period)
        & has_earner
        & ~benunit("housing_benefit_pension_age_regulations_apply", period)
    )
    for rates, share in fiscal_year_segments(schedule, period.start.year):
        couple_amount = select(
            [older, eldest >= p.age_threshold.younger],
            [rates.couple_older, rates.couple_younger],
            default=rates.couple_minors,
        )
        weekly = select(
            [benunit("is_lone_parent", period), benunit("is_couple", period)],
            [
                where(older, rates.lone_parent_older, rates.lone_parent_younger),
                couple_amount,
            ],
            default=where(older, rates.single_older, rates.single_younger),
        )
        amount = where(applies, weekly * WEEKS_IN_YEAR, 0)
        yield hb_apply_defined_for(benunit, period, name, amount), share


class housing_benefit_specified_or_temporary_accommodation_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit specified or temporary accommodation earnings disregard"
    documentation = (
        "The amount, from 5 October 2026, that the working-age Regulations "
        "disregard from the net earnings of a claimant who lives in specified "
        "or temporary accommodation where the claimant or partner is an "
        "employed or self-employed earner: £61.41 a week for a single "
        "claimant or lone parent under 25 and £77.73 at 25 or over; for a "
        "couple, £97.33 where both are under 18, £61.53 where one is 18 or "
        "over but both are under 25, and £119.70 where one is 25 or over. A "
        "couple has one amount, taken from the claimant's earnings and then "
        "from the partner's. This is the full amount; "
        "housing_benefit_applicable_income_disregard adds it to the other "
        "disregards and caps the total at net earnings. The pension-age "
        "Regulations have no such disregard. This annual output combines "
        "the full amounts over their effective-date segments. The earnings "
        "limits and award are calculated separately within each segment, "
        "with annual earnings and household circumstances held constant."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2026/753/regulation/2",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/nisr/2026/157/regulation/2",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
    )

    def formula(benunit, period, parameters):
        return sum(
            amount * share
            for amount, share in hb_accommodation_segments(benunit, period, parameters)
        )
