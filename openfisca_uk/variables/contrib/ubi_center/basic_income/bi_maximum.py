from openfisca_uk.model_api import *


class bi_maximum(Variable):
    label = "Basic income before phase-outs"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        bi = parameters(period).contrib.ubi_center.basic_income
        is_senior_for_bi = person("is_SP_age", period)
        is_child_for_bi = person("age", period) < bi.amount.adult_age
        is_wa_for_bi = ~is_senior_for_bi & ~is_child_for_bi
        return (
            select(
                [is_child_for_bi, is_wa_for_bi, is_senior_for_bi],
                [
                    bi.amount.by_age.child,
                    bi.amount.by_age.working_age,
                    bi.amount.by_age.senior,
                ],
            )
            * WEEKS_IN_YEAR
        )
