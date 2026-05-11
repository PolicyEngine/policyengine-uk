from policyengine_uk.model_api import *


class tewkesbury_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Tewkesbury's Universal Credit regulation 60A pensioner exception"
        " applies"
    )
    documentation = "Default Scheme paragraph 3(2)(b) keeps a pension-age claimant on the prescribed pensioner scheme where their Universal Credit award arises from regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014, which Tewkesbury has adopted unchanged."
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/3"
    default_value = False
