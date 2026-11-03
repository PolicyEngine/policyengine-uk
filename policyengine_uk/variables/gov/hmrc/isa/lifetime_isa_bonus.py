from policyengine_uk.model_api import *


class lifetime_isa_bonus(Variable):
    value_type = float
    entity = Person
    label = "Lifetime ISA government bonus"
    documentation = "Government contribution to qualifying Lifetime ISA additions. This capital transfer is counted in government spending but not household current income; it does not automatically update a supplied account balance."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/1"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.isa.lifetime
        if not p.in_effect:
            return 0
        age = person("age", period)
        eligible = (age >= p.minimum_age) & (age < p.payment_age_limit)
        payments = max_(person("lifetime_isa_payments", period), 0)
        return eligible * min_(payments, p.payment_limit) * p.bonus_rate
