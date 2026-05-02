from policyengine_uk.model_api import *


class babergh_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Babergh CTR non-dependant Universal Credit assessed earned income"
    documentation = "Source input for person-level earned income used in the non-dependant's Universal Credit award calculation."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.babergh.gov.uk/documents/d/babergh/bdc-ctr-scheme-2026_27-v4-pdf"
    )

    def formula(person, period, parameters):
        return person("employment_income", period) + person(
            "self_employment_income", period
        )
