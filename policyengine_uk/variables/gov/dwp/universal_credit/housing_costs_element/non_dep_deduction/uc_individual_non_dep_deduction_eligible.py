from policyengine_uk.model_api import *


class uc_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible person for the Universal Credit non-dependent deduction"
    documentation = (
        "A non-dependant of a renter, aged 21 or over and not otherwise "
        "exempt: either a member of another family who is not liable for rent "
        "(see is_non_dependant_of_household_head) or a member of their own "
        "benefit unit who is not the claimant, partner or a qualifying young "
        "person (see is_benefit_unit_non_dependant_for_universal_credit)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
        non_dependant = person("is_non_dependant_of_household_head", period) | person(
            "is_benefit_unit_non_dependant_for_universal_credit", period
        )
        age_eligible = person("age", period) >= p.age_threshold
        exempt = person("uc_non_dep_deduction_exempt", period)
        return non_dependant & age_eligible & ~exempt
