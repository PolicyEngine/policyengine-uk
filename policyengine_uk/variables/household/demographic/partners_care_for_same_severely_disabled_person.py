from policyengine_uk.model_api import *


class partners_care_for_same_severely_disabled_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claimant and partner care for the same severely disabled person"
    documentation = (
        "Whether the claimant and partner who both care are caring for the "
        "same severely disabled person. In law only one of them can then be "
        "entitled to Carer's Allowance (SSCBA 1992 s.70(7ZA)) or Carer "
        "Support Payment (SSI 2023/302 reg 5(3)), so only one satisfies the "
        "legacy carer premium condition, and Scottish working-age council tax "
        "reduction pays one premium (SSI 2021/249 Sch 1 para 5(3)-(4)). "
        "Unless supplied, it is true unless at least two of the claimant and "
        "partner are carers with a reported Carer's Allowance or Carer "
        "Support Payment award (carers_allowance_reported, the model's "
        "reported-receipt input for both): two awards mean two different "
        "people cared for, while caring hours cannot show who is cared for. "
        "With more than two members supplied as claimant or partner, two "
        "awards make the default false for all of them. The "
        "model's carers_allowance and carer_support_payment are paid on "
        "caring hours or a reported award, and do not read this variable."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/5",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
    )

    def formula(benunit, period, parameters):
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        reported_award = benunit.members("carers_allowance_reported", period) > 0
        carer = benunit.members("is_carer_for_benefits", period)
        return benunit.sum(claimant_or_partner & carer & reported_award) < 2
