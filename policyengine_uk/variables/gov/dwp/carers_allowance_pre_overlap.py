from policyengine_uk.model_api import *
from policyengine_uk.utils.couple_carer_award import limit_carer_benefit_to_one_partner


class carers_allowance_pre_overlap(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance before the overlapping-benefit adjustment"
    documentation = (
        "The same-person couple restriction is applied before overlapping "
        "benefits, using the reported-award/head modelling convention described "
        "in the carer benefit assumptions. "
        "The Carer's Allowance a person is entitled to before the Social "
        "Security (Overlapping Benefits) Regulations 1979 reduce it by another "
        "personal benefit. A person whose allowance is reduced to nil keeps "
        "this underlying entitlement. is_entitled_to_carer_benefit combines "
        "the pre-overlap amounts and any benefit in payment for rules that "
        "test entitlement. carers_allowance is the amount payable."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/70",
    )

    def formula(person, period, parameters):
        candidate = person("carers_allowance_pre_couple_limit", period)
        return limit_carer_benefit_to_one_partner(person, period, candidate)
