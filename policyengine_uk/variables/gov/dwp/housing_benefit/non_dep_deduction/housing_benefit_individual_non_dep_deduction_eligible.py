from policyengine_uk.model_api import *


class housing_benefit_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for the Housing Benefit non-dependent deduction"
    documentation = (
        "A non-dependant aged 18 or over: either a member of another family "
        "who is not liable for rent (see is_non_dependant_of_household_head) "
        "or a member of their own benefit unit who is not the claimant, "
        "partner or a child or young person (see "
        "is_benefit_unit_non_dependant_for_legacy_benefits)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        non_dependant = person("is_non_dependant_of_household_head", period) | person(
            "is_benefit_unit_non_dependant_for_legacy_benefits", period
        )
        age_eligible = person("age", period) >= p.age_threshold
        exempt = person("housing_benefit_non_dep_deduction_exempt", period)
        return non_dependant & age_eligible & ~exempt
