from policyengine_uk.model_api import *


class council_tax_reduction_working_age_has_universal_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a Universal Credit award for working-age council tax reduction"
    documentation = (
        "Whether the claimant or partner has an award of Universal Credit, "
        "which moves a working-age council tax reduction claim onto the "
        "Universal Credit income rules in Scotland and Wales."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/42",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
    )

    def formula(benunit, period, parameters):
        return benunit("is_uc_entitled", period)
