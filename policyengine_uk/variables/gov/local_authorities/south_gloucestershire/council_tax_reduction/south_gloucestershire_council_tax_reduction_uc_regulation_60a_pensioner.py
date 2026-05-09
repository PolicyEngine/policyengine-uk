from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "South Gloucestershire CTR pensioner protected by Universal Credit regulation 60A"
    definition_period = YEAR
    reference = "https://beta.southglos.gov.uk/static/f7a9a3f9b402fb3e3ae79fd5c297b695/Council_tax_reduction_scheme_rules_pensioners.pdf"
    documentation = (
        "Whether the applicant remains in South Gloucestershire's pensioner "
        "scheme despite Universal Credit under the source-listed regulation 60A "
        "protection."
    )
