from policyengine_uk.model_api import *


def state_pension_overlapping_part(person, period, age_addition_overlaps: bool):
    """The State Pension that overlaps with a carer benefit.

    A new State Pension overlaps in full, including any protected payment
    above the full rate. An old State Pension overlaps without its additional
    pension, and with or without its age addition as the carer benefit's own
    rules say. state_pension can scale its components (a contributed reform
    does), so the parts that do not overlap are taken as a share of them.
    """
    state_pension = person("state_pension", period)
    additional = person("additional_state_pension", period)
    age_addition = person("state_pension_age_addition", period)
    components = add(
        person,
        period,
        [
            "basic_state_pension",
            "new_state_pension",
            "additional_state_pension",
            "state_pension_age_addition",
        ],
    )
    pension_type = person("state_pension_type", period)
    old_system = pension_type == pension_type.possible_values.BASIC
    not_overlapping = old_system * additional
    if not age_addition_overlaps:
        not_overlapping = not_overlapping + age_addition
    not_overlapping_share = np.divide(
        not_overlapping,
        components,
        out=np.zeros_like(components, dtype=float),
        where=components > 0,
    )
    return state_pension * (1 - not_overlapping_share)


class overlapping_state_pension(Variable):
    value_type = float
    entity = Person
    label = "State Pension that overlaps with Carer's Allowance"
    documentation = (
        "The State Pension by which Carer's Allowance is reduced. A new State "
        "Pension under Part 1 of the Pensions Act 2014 overlaps in full, "
        "including any protected payment above the full rate. An old State "
        "Pension overlaps without its additional pension or its age addition. "
        "When only a reported total is available, the model estimates its "
        "basic component up to the full basic rate and treats the excess as "
        "additional pension. This split cannot identify basic-pension "
        "increments above that rate or additional pension within a partial "
        "pension below it. A State Pension supplied directly, with no "
        "components, overlaps in full as an input convention."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/4",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/12",
        "https://www.legislation.gov.uk/uksi/1979/597/schedule/1",
    )

    def formula(person, period, parameters):
        # An age addition is adjusted only by reference to another age
        # addition (SI 1979/597 reg 4(3); Sch 1 row 4, "except any age
        # addition"), so it never reduces Carer's Allowance.
        return state_pension_overlapping_part(
            person, period, age_addition_overlaps=False
        )
