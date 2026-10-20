from policyengine_uk.model_api import *


class overlapping_state_pension(Variable):
    value_type = float
    entity = Person
    label = "State Pension that overlaps with carer benefits"
    documentation = (
        "The State Pension by which Carer's Allowance and Carer Support Payment "
        "are reduced. A new State Pension under Part 1 of the Pensions Act 2014 "
        "overlaps in full, including any protected payment above the full rate. "
        "An old State Pension overlaps without its additional pension. When "
        "only a reported total is available, the model estimates its basic "
        "component up to the full basic rate and treats the excess as "
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
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
    )

    def formula(person, period, parameters):
        state_pension = person("state_pension", period)
        additional = person("additional_state_pension", period)
        components = add(
            person,
            period,
            ["basic_state_pension", "new_state_pension", "additional_state_pension"],
        )
        pension_type = person("state_pension_type", period)
        old_system = pension_type == pension_type.possible_values.BASIC
        # state_pension can scale its components (a contributed reform does),
        # so take the additional pension as a share of them.
        additional_share = np.divide(
            additional,
            components,
            out=np.zeros_like(components, dtype=float),
            where=components > 0,
        )
        return state_pension * (1 - old_system * additional_share)
