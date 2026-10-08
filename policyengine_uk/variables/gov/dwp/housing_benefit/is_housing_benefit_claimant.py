from policyengine_uk.model_api import *


class is_housing_benefit_claimant(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Housing Benefit claimant"
    documentation = "Identifies the person making the Housing Benefit claim. Defaults to the benefit-unit head among claimant/partner members, or their eldest member; supply explicitly when the partner claims. This is not inferred from ESA receipt."
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/82"

    def formula(person, period, parameters):
        adults = person("is_claimant_or_partner", period)
        heads = adults & person("is_benunit_head", period)
        pool = where(person.benunit.any(heads), heads, adults)
        return pool & (
            person.get_rank(person.benunit, -person("age", period), condition=pool) == 0
        )
