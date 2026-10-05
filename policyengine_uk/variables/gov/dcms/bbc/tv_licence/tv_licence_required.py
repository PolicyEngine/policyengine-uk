from policyengine_uk.model_api import *


class tv_licence_required(Variable):
    label = "TV licence required"
    documentation = (
        "Whether anyone in the household watches or records live television "
        "or uses BBC iPlayer. When this is not provided directly, television "
        "ownership is used as a backward-compatible proxy."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/363",
        "https://www.legislation.gov.uk/uksi/2016/704/regulation/9/made",
    )

    def formula(household, period, parameters):
        return household("household_owns_tv", period)
