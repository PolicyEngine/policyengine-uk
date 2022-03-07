from openfisca_uk.model_api import *


class hb_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Non-dependent deduction (individual)"
    documentation = "The non-dependent deduction to make from other families' Housing Benefit claims in respect of this person."
    definition_period = YEAR
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/74/made"

    def formula(person, period, parameters):
        non_dep = parameters(period).dwp.housing_benefit.non_dependent
        meets_age_condition = person("age", period) >= non_dep.age
        exempt = add(person, period, non_dep.exemptions) > 0
        is_non_dep = meets_age_condition & ~exempt
        weekly_income = person("total_income", period) / WEEKS_IN_YEAR
        deduction = non_dep.deduction.calc(weekly_income) * WEEKS_IN_YEAR
        return deduction * is_non_dep