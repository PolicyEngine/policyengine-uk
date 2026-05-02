from policyengine_uk.model_api import *


class ipswich_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Ipswich CTR non-dependant Universal Credit assessed earned income"
    documentation = "Source input for person-level earned income used in the non-dependant's Universal Credit award calculation."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.ipswich.gov.uk/sites/ipswich/files/2026-03/Council%20Tax%20Reduction%20scheme%202026_0.pdf"

    def formula(person, period, parameters):
        return person("employment_income", period) + person(
            "self_employment_income", period
        )
