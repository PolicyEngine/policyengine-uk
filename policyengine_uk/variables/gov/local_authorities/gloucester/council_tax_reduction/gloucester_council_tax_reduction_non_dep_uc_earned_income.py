from policyengine_uk.model_api import *


class gloucester_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = (
        "Gloucester Council Tax Support non-dependant Universal Credit earned income"
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.gloucester.gov.uk/media/ruwinppa/local-council-tax-support-policy-2026-v2.pdf"
    documentation = (
        "Source input for the UC earned-income estimate used to decide whether a "
        "Gloucester non-dependant with a Universal Credit award is in remunerative work."
    )

    def formula(person, period, parameters):
        return person("uc_mif_capped_earned_income", period)
