from policyengine_uk.model_api import *


def create_cb_hitc_household_based() -> Reform:
    """
    Reform that makes Child Benefit HITC assessed on household income
    rather than individual income.

    Policy: Assess CB-HITC based on combined household income rather than
    the highest individual earner's income.

    Source: Conservative Party proposal
    """

    class CB_HITC(Variable):
        value_type = float
        entity = Person
        label = "Child Benefit High-Income Tax Charge"
        definition_period = YEAR
        reference = (
            "https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8"
        )
        unit = GBP
        defined_for = "is_higher_earner"

        def formula(person, period, parameters):
            CB_received = person.benunit("child_benefit", period)
            hitc = parameters(period).gov.hmrc.income_tax.charges.CB_HITC
            personal_income = person("adjusted_net_income", period)
            income = person.benunit.sum(personal_income)
            percentage = max_(income - hitc.phase_out_start, 0) / (
                hitc.phase_out_end - hitc.phase_out_start
            )
            return min_(percentage, 1) * CB_received

    class reform(Reform):
        def apply(self):
            self.update_variable(CB_HITC)

    return reform


def create_household_based_hitc_reform(
    parameters, period, bypass: bool = False
):
    if bypass:
        return create_cb_hitc_household_based()

    if parameters(period).gov.contrib.conservatives.cb_hitc_household:
        return create_cb_hitc_household_based()
    else:
        return None


# For direct import
cb_hitc_household_based_reform = create_cb_hitc_household_based()
