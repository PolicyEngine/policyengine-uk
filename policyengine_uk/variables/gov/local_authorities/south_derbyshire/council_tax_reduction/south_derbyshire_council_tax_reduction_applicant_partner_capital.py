from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_applicant_partner_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire CTR applicant and partner source-reported capital"
    documentation = "Use this input when child, young-person, or non-dependant capital is included in household savings, because South Derbyshire assesses applicant and partner capital and ignores child or young-person capital."
    definition_period = YEAR
    unit = GBP
    default_value = -1
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"
