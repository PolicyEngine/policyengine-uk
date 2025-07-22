from policyengine_uk.model_api import *


class cb_hitc(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit High-Income Tax Charge"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8"
    unit = GBP
    defined_for = "is_higher_earner"

    def formula(person, period, parameters):
        CB_received = person.benunit("child_benefit", period)
        p = parameters(period).gov.hmrc.income_tax.charges.cb_hitc
        income = person("adjusted_net_income", period)
        percentage = max_(income - p.phase_out_start, 0) / (
            p.phase_out_end - p.phase_out_start
        )
        return min_(percentage, 1) * CB_received
