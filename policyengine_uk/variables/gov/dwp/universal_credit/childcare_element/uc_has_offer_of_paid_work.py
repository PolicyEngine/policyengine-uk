from policyengine_uk.model_api import *


class uc_has_offer_of_paid_work(Variable):
    value_type = bool
    entity = Person
    label = "Has an offer of paid work due to start before the end of the next Universal Credit assessment period"
    documentation = (
        "Regulation 32(1)(a): a claimant with an offer of paid work due to "
        "start before the end of the next assessment period meets the "
        "claimant's limb of the childcare work condition. It does not meet "
        "the other member's limb in regulation 32(1)(b). Survey data does not "
        "record offers of work, so this defaults to false."
    )
    definition_period = YEAR
    default_value = False
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 32(1)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/32",
        ),
        dict(
            title="Advice for Decision Making ch. F7, paras. F7011-F7012",
            href="https://assets.publishing.service.gov.uk/media/696a076c7b7f37aa8e4022d9/adm-ch-f7.pdf",
        ),
    ]
