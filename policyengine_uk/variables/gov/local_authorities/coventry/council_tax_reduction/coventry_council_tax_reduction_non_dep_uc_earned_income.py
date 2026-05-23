from policyengine_uk.model_api import *


class coventry_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Coventry CTR non-dependant Universal Credit assessed earned income"
    documentation = "Source input for person-level earned income used in the non-dependant's Universal Credit award calculation."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.coventry.gov.uk/downloads/file/46761/council-tax-support-scheme-2026-to-2027"

    def formula(person, period, parameters):
        return person("employment_income", period) + person(
            "self_employment_income", period
        )
