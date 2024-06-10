from policyengine_uk.model_api import *


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
        household_based = parameters(
            period
        ).gov.contrib.conservatives.cb_hitc_household
        personal_income = person("adjusted_net_income", period)
        if household_based:
            income = person.benunit.sum(personal_income)
        else:
            income = personal_income
        percentage = max_(income - hitc.phase_out_start, 0) / (hitc.phase_out_end - hitc.phase_out_start)
        return min_(percentage, 1) * CB_received
