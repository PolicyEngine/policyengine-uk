from policyengine_uk.model_api import *
import warnings


class bi_household_phaseout(Variable):
    label = "Basic income phase-out (household)"
    documentation = (
        "Reduction in basic income from household-level phase-outs."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        income = person("total_income", period)
        household = person.household
        household_income = household.sum(income)
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        remaining_bi = person("bi_maximum", period) - person(
            "bi_individual_phaseout", period
        )  # Basic income remaining after individual-level phaseouts

        household_bi = household.sum(remaining_bi)
        income_over_threshold = max_(
            household_income - bi.phase_out.household.threshold,
            0,
        )
        uncapped_deduction = (
            bi.phase_out.household.rate * income_over_threshold
        )
        capped_deduction = min_(household_bi, uncapped_deduction)

        warnings.filterwarnings("ignore")

        percent_reduction = where(
            household_bi > 0, capped_deduction / household_bi, 0
        )
        return percent_reduction * remaining_bi
