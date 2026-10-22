from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    applicant_family,
)


class council_tax_reduction_working_age_has_universal_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a Universal Credit award for working-age council tax reduction"
    documentation = (
        "Whether the applicant or partner has an award of Universal Credit "
        "(not a household head who applies alone, whose benefit unit's award "
        "is its claimant's), "
        "which moves a working-age council tax reduction claim onto the "
        "Universal Credit income rules in Scotland and Wales."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/42",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
    )

    def formula(benunit, period, parameters):
        # Universal Credit is the benefit unit's claimant's and partner's,
        # not a household head's who applies alone.
        return benunit("is_uc_entitled", period) & applicant_family(benunit, period)
