from policyengine_uk.model_api import *


class individual_scp(Variable):
    entity = Person
    label = "Individual SCP amount"
    definition_period = WEEK
    value_type = float
    unit = GBP


    def formula(person, period, parameters):
        age = person("age", period)
        year_after_death = person("year_after_death", period) # Assuming you have this variable defined
        if age > parameters(period).SCP.criteria.age_limit:
            return 0
        amount = parameters(period).SCP.amount.amount

        if year_after_death > 0 and year_after_death <= parameters(period).SCP.criteria.payment_period_after_death:
            amount *= parameters(period).SCP.amount.payment_multiplier_after_death

        return amount
