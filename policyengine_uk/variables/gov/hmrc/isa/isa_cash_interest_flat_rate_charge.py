from policyengine_uk.model_api import *


class isa_cash_interest_flat_rate_charge(Variable):
    value_type = float
    entity = Person
    label = "Final charge on cash interest in non-cash ISAs"
    documentation = "Final manager-paid charge on the of-which cash-interest component of non-cash ISAs from fiscal 2027-28. This tax on an income return enters government and household taxes separately from ordinary income tax."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/2026/1018/regulation/15/made"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc
        if not p.isa.cash_interest_charge.in_effect:
            return 0
        interest = max_(person("non_cash_isa_cash_interest", period), 0)
        return interest * p.income_tax.rates.savings.basic
