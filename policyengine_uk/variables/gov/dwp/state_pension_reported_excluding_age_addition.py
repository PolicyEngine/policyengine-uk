from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.state_pension_age_addition import (
    receives_age_addition,
)


class state_pension_reported_excluding_age_addition(Variable):
    label = "reported State Pension excluding the age addition"
    documentation = (
        "state_pension_reported less the age addition it is taken to include. "
        "The survey records the State Pension a person receives, which for a "
        "basic State Pension recipient over 80 includes the 25p a week age "
        "addition. basic_state_pension, new_state_pension and "
        "additional_state_pension split this amount, and "
        "state_pension_age_addition pays the addition, so it is neither "
        "counted twice nor uprated as additional pension."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/79"

    def formula(person, period, parameters):
        reported = person("state_pension_reported", period)
        # state_pension_reported was observed under the legislated rules, so
        # take off the legislated age addition, not a reformed one, as the
        # components split it at the legislated full rate
        # (PolicyEngine/policyengine-uk#2122).
        baseline = getattr(person.simulation, "baseline", None)
        legislated = (
            baseline.tax_benefit_system.parameters
            if baseline is not None
            else parameters
        )
        p = legislated(period).gov.dwp.state_pension.age_addition
        included = (
            receives_age_addition(person, period, p.age, period)
            * p.amount
            * WEEKS_IN_YEAR
        )
        return max_(reported - included, 0)
