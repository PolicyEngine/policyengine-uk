from policyengine_uk.model_api import *
import warnings


class bi_individual_phaseout(Variable):
    label = "Basic income phase-out (individual)"
    documentation = (
        "Reduction in basic income from individual-level phase-outs."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        income = person("total_income", period)
        p = parameters(period).gov.contrib.ubi_center.basic_income
        max_bi = person("bi_maximum", period)
        income_over_threshold = max_(
            income - p.phase_out.individual.threshold, 0
        )
        uncapped_deduction = (
            p.phase_out.individual.rate * income_over_threshold
        )
        return min_(max_bi, uncapped_deduction)
