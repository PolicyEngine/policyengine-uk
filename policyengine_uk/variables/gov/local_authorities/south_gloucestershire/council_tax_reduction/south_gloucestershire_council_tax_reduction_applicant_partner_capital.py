from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_applicant_partner_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "South Gloucestershire CTR applicant and partner capital"
    definition_period = YEAR
    unit = GBP
    default_value = -1
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"
    documentation = (
        "Source input for capital held by the applicant and partner. Use -1 to "
        "fall back to the household savings proxy."
    )
