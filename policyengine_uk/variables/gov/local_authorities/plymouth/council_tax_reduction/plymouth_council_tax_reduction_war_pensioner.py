from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_war_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Plymouth Council Tax Support claimant or partner is in the war pensioner income-band class"
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
