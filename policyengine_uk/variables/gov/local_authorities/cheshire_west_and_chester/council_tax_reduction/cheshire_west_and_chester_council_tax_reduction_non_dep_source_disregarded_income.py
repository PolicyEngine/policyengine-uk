from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_non_dep_source_disregarded_income(
    Variable
):
    value_type = float
    entity = Person
    label = "Cheshire West and Chester CTR source-disregarded annual non-dependant gross income"
    documentation = "Use this input for source-listed non-dependant gross-income disregards not otherwise represented in PolicyEngine UK, such as disability benefits listed in paragraph 33.7."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"
    default_value = 0
