from policyengine_uk.model_api import *
from policyengine_uk.utils.child_benefit import (
    child_benefit_charge_percentage,
    round_down_to_pounds,
)


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit High-Income Tax Charge"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8"
    unit = GBP
    defined_for = "is_higher_earner"

    def formula(person, period, parameters):
        CB_received = person.benunit("child_benefit", period)
        hitc = parameters(period).gov.hmrc.income_tax.charges.CB_HITC
        personal_income = person("adjusted_net_income", period)
        income = person.benunit.sum(personal_income)
        # The same s. 681C(3) rounding as the baseline charge, on the
        # household's combined income.
        percentage = child_benefit_charge_percentage(
            income, hitc.phase_out_start, hitc.phase_out_end
        )
        return round_down_to_pounds(percentage * round_down_to_pounds(CB_received))


class make_cb_hitc_household_based(Variable):
    def apply(self):
        self.update_variable(CB_HITC)


def create_household_based_hitc_reform(parameters, period):
    if parameters(period).gov.contrib.conservatives.cb_hitc_household:
        return make_cb_hitc_household_based
    else:
        return None
