from policyengine_uk.model_api import *


class bi_maximum(Variable):
    label = "Basic income before phase-outs"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        weekly_flat_amount = bi.amount.flat
        is_senior_for_bi = person("is_SP_age", period)
        age = person("age", period)
        is_child_for_bi = (age < bi.amount.adult_age) * (
            age >= bi.amount.child_min_age
        )
        is_adult_for_bi = (age >= bi.amount.adult_age) * ~is_senior_for_bi
        weekly_amount_by_age = select(
            [is_child_for_bi, is_senior_for_bi, is_adult_for_bi],
            [
                bi.amount.by_age.child,
                bi.amount.by_age.senior,
                bi.amount.by_age.working_age,
            ],
        )
        return (weekly_flat_amount + weekly_amount_by_age) * WEEKS_IN_YEAR
