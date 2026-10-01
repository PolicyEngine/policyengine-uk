from policyengine_uk.model_api import *


class carers_allowance_pre_overlap(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance before the overlapping-benefit adjustment"
    documentation = (
        "The Carer's Allowance a person is entitled to before the Social "
        "Security (Overlapping Benefits) Regulations 1979 reduce it by another "
        "personal benefit. A person whose allowance is reduced to nil keeps "
        "this underlying entitlement, which is what carer premiums, the "
        "Pension Credit carer addition and the benefit cap exemption look at. "
        "carers_allowance is the amount payable."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/70"

    def formula(person, period, parameters):
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        csp_replaces_ca = period.start.year >= 2025
        receives_ca = person("carers_allowance_reported", period) > 0
        ca = parameters(period).gov.dwp.carers_allowance
        weekly_care_hours = person("care_hours", period)
        meets_work_condition = weekly_care_hours >= ca.min_hours
        would_claim = person("would_claim_carers_allowance", period)
        eligible = (
            ~(in_scotland & csp_replaces_ca)
            & (meets_work_condition | receives_ca)
            & would_claim
        )
        return eligible * ca.rate * WEEKS_IN_YEAR
