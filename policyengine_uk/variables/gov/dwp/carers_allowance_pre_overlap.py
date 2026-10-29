from policyengine_uk.model_api import *
from policyengine_uk.utils.carers_allowance_taper import (
    carers_allowance_annual_award,
    carers_allowance_shares_of_year,
    carers_allowance_weekly_by_part_of_year,
    carries_parts_of_year,
)
from policyengine_uk.utils.couple_carer_award import limit_carer_benefit_to_one_partner
from policyengine_uk.variables.gov.dwp.carers_allowance_pre_couple_limit import (
    carers_allowance_pre_couple_limit,
)


class carers_allowance_pre_overlap(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance before the overlapping-benefit adjustment"
    documentation = (
        "The model applies the same-person couple restriction before "
        "overlapping benefits, giving the award to the partner the couple "
        "would elect, as the carer benefit assumptions describe. "
        "The Carer's Allowance a person is entitled to before the Social "
        "Security (Overlapping Benefits) Regulations 1979 reduce it by another "
        "personal benefit. A person whose allowance overlapping benefits "
        "reduce to nil keeps this underlying entitlement. is_entitled_to_carer_benefit combines "
        "the pre-overlap amounts and any benefit in payment for rules that "
        "test entitlement. carers_allowance is the amount payable. In the "
        "year the Budget 2026 earnings taper starts, the couple restriction "
        "works on the weeks before the taper and the weeks under it "
        "separately; a partner below the earnings limit has the larger award "
        "in both, so, where the model reads the earnings above the limit "
        "itself, one partner has the award for the year. A "
        "carers_allowance_pre_couple_limit that an input supplies, or that a "
        "reform neutralizes, calculates with a formula of its own or "
        "otherwise changes (with defined_for, say), carries no dates, so the "
        "restriction applies to the benefit unit's awards for the whole year."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/70",
    )

    def formula(person, period, parameters):
        candidate = person("carers_allowance_pre_couple_limit", period)
        whole_year = limit_carer_benefit_to_one_partner(person, period, candidate)
        parts = carers_allowance_weekly_by_part_of_year(person, period, parameters)
        if len(parts) == 1:
            return whole_year
        # In the year the earnings taper starts, a person keeps their award
        # for the parts of the year the restriction picks them in.
        candidate_share, kept_share = carers_allowance_shares_of_year(
            person, period, parts
        )
        by_parts = carries_parts_of_year(
            person,
            period,
            carers_allowance_pre_couple_limit,
            candidate,
            carers_allowance_annual_award(parts),
        ) & (candidate_share > 0)
        kept = kept_share / where(by_parts, candidate_share, 1)
        return where(by_parts, candidate * kept, whole_year)
