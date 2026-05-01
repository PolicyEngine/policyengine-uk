from policyengine_uk.model_api import *


class enfield_council_tax_reduction_war_widow(Variable):
    value_type = bool
    entity = BenUnit
    label = "Enfield CTR war widow protected group"
    definition_period = YEAR
    reference = "https://www.enfield.gov.uk/__data/assets/pdf_file/0019/126262/Council-tax-reduction-scheme-2026-to-2027-Benefits-and-money-advice.pdf"
