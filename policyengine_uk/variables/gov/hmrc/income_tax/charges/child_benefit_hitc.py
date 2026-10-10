from policyengine_uk.model_api import *
from policyengine_uk.utils.child_benefit import child_benefit_charge_share


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
        income = person("adjusted_net_income", period)
        percentage = child_benefit_charge_share(
            income, hitc.phase_out_start, hitc.phase_out_end
        )
        return percentage * CB_received
