from openfisca_uk.model_api import *


class HB_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Non-dependent deduction (individual)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("benunit_rent", period) == 0
        over_21 = person("age", period) >= 21
        deduction_scale = parameters(
            period
        ).benefit.housing_benefit.deductions.non_dep_deduction
        weekly_income = person("total_income", period)
        deduction = deduction_scale.calc(weekly_income)
        return deduction * over_21 * not_rent_liable * MONTHS_IN_YEAR


class HB_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Non-dependent deductions"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(
                benunit.members("HB_individual_non_dep_deduction", period)
            )
        )
        non_dep_deductions_in_bu = aggr(
            benunit, period, ["HB_individual_non_dep_deduction"]
        )
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu

