from policyengine_uk.model_api import *
from policyengine_uk.utils.couple_carer_award import limit_carer_benefit_to_one_partner


class carer_support_payment_pre_overlap(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment before the overlapping-benefit reduction"
    documentation = (
        "The same-person couple restriction is applied before overlapping "
        "benefits, using the reported-award/head modelling convention described "
        "in the carer benefit assumptions. "
        "The Carer Support Payment component a carer in Scotland is entitled "
        "to before regulation 16(2) of the Carer Support Payment Regulations "
        "reduces it by an overlapping benefit. A carer whose payment is "
        "reduced to £0 keeps this underlying entitlement. "
        "carer_support_payment is the amount given. The earnings condition uses "
        "the existing annual Carer's Allowance net-earnings reader, spread "
        "evenly over 52 weeks. This approximates constant earnings; it cannot "
        "resolve the award-week or, from 16 November 2025, preceding-award-week "
        "assessment for varying earnings. The reader's standard-code PAYE and "
        "unrepresented care-charge/disregard assumptions also apply."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/asp/2018/9/part/4",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/3",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/4",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/5",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/14",
        "https://www.legislation.gov.uk/ssi/2023/302/schedule/2/paragraph/4",
    )

    def formula(person, period, parameters):
        candidate = person("carer_support_payment_pre_couple_limit", period)
        return limit_carer_benefit_to_one_partner(person, period, candidate)
