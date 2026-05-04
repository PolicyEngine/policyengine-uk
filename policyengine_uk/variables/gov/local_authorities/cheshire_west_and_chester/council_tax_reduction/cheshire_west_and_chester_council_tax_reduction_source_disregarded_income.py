from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_source_disregarded_income(
    Variable
):
    value_type = float
    entity = BenUnit
    label = "Cheshire West and Chester CTR source-disregarded annual income"
    documentation = "Use this input for source-listed income disregards not otherwise represented in PolicyEngine UK, such as fully disregarded war pensions or old Council Tax Benefit non-earnings disregards."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-1.pdf"
    default_value = 0
