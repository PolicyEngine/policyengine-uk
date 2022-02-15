from openfisca_uk.model_api import *


class bi_phaseout(Variable):
    label = "Basic income phase-out"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(person, period, parameters):
        income = person("total_income", period)
        bi = parameters(period).contrib.ubi_center.basic_income
        max_bi = person("bi_maximum", period)
        income_over_threshold = max_(income - bi.phase_out.threshold, 0)
        uncapped_deduction = bi.phase_out.rate * income_over_threshold
        return min_(max_bi, uncapped_deduction)
