from openfisca_uk.model_api import *


class HB_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Non-dependent deduction (individual)"
    documentation = "The non-dependent deduction to made from this individual's family's Housing Benefit claim."
    definition_period = YEAR
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/74/made"

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("hb_eligible_rent", period) == 0
        non_dep = parameters(period).dwp.housing_benefit.non_dependent
        meets_age_condition = person("age", period) >= non_dep.age
        exempt = any_(person, period, non_dep.exemptions)
        is_non_dep = not_rent_liable & meets_age_condition & ~exempt
        weekly_income = person("total_income", period) / WEEKS_IN_YEAR
        deduction = non_dep.deduction.calc(weekly_income)
        return deduction * is_non_dep * MONTHS_IN_YEAR


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

