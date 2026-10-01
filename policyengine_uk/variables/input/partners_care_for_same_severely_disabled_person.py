from policyengine_uk.model_api import *


class partners_care_for_same_severely_disabled_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claimant and partner care for the same severely disabled person"
    documentation = (
        "Whether the claimant and partner who both care are caring for the "
        "same severely disabled person. Only one of them can then be entitled "
        "to Carer's Allowance or Carer Support Payment for that person "
        "(SSCBA 1992 s.70(7ZA)), and Scottish working-age council tax "
        "reduction pays the carer premium for one of them (SSI 2021/249 Sch 1 "
        "para 5(3)-(4)), so the legacy carer premium is paid once. Two "
        "partners who both receive Carer's Allowance cannot be caring for the "
        "same person. Defaults to false: partners who both care are treated "
        "as caring for different people."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
    )
