from policyengine_uk.model_api import *


class travel_grant_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for Travel Grant"
    documentation = (
        "Whether the person is eligible for Student Finance England Travel Grant. "
        "This first-pass model uses explicit placement inputs, the published England coverage rule, "
        "the clinical-placement NHS-bursary exclusion, and a maintenance-loan proxy for income-assessed support."
    )
    definition_period = YEAR
    defined_for = "would_claim_travel_grant"

    def formula(person, period, parameters):
        country = person.household("country", period)
        in_england = country == country.possible_values.ENGLAND

        abroad_placement = person("travel_grant_abroad_placement", period)
        clinical_placement = person("travel_grant_clinical_placement", period)
        receives_nhs_bursary = person(
            "travel_grant_receives_means_tested_nhs_bursary", period
        )
        income_assessed_support = person("travel_grant_income_assessed_support", period)
        expenses = person("travel_grant_eligible_expenses", period)

        clinical_path = (
            clinical_placement & income_assessed_support & ~receives_nhs_bursary
        )

        return in_england & (abroad_placement | clinical_path) & (expenses > 0)
