from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Plymouth Council Tax Support non-dependant Universal Credit assessed earned income"
    documentation = "Source input for person-level earned income used in the non-dependant's Universal Credit award calculation."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"

    def formula(person, period, parameters):
        return person("employment_income", period) + person(
            "self_employment_income", period
        )
