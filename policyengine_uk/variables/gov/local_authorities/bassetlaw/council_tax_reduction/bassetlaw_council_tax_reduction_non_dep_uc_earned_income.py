from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_non_dep_uc_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Bassetlaw Council Tax Reduction non-dependant Universal Credit assessed earned income"
    documentation = "Source input for whether a non-dependant's UC award is calculated on the basis that the person has earned income."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(person, period, parameters):
        return person("employment_income", period) + person(
            "self_employment_income", period
        )
