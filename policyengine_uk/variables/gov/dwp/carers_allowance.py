from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import HALF_PENNY
from policyengine_uk.utils.carers_allowance_taper import (
    carers_allowance_annual_award,
    carers_allowance_shares_of_year,
    calculated_by_model,
    carers_allowance_weekly_by_part_of_year,
    carries_parts_of_year,
)
from policyengine_uk.variables.gov.dwp.carers_allowance_pre_couple_limit import (
    carers_allowance_pre_couple_limit,
)
from policyengine_uk.variables.gov.dwp.carers_allowance_pre_overlap import (
    carers_allowance_pre_overlap,
)


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance"
    documentation = (
        "Carer's Allowance payable after the overlapping-benefit adjustment: "
        "any other personal benefit that overlaps with it, such as State "
        "Pension, reduces the allowance, and the model pays only the balance. "
        "The model compares annual amounts, which gives the weekly rule's "
        "result when the overlapping benefit pays a constant rate all year. "
        "Where the overlapping benefit exceeds the carer rate in some weeks "
        "and falls short of it or stops in others, for example when it starts "
        "partway through the year, the annual comparison pays less than the "
        "weekly rule would; annual inputs carry no dates to do better. In the "
        "year the Budget 2026 earnings taper starts, overlapping benefits "
        "come off only for the share of the year the allowance pays for. A "
        "carers_allowance_pre_overlap or carers_allowance_pre_couple_limit "
        "that an input supplies, or that a reform neutralizes, calculates "
        "with a formula of its own or otherwise changes, carries no dates, so "
        "the whole year's overlapping benefits come off the award; the payment "
        "reads the stage before the couple restriction only where the model "
        "calculates the award before overlap. Less than half a penny for the "
        "year is nil."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/4",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/12",
    )

    def formula(person, period, parameters):
        pre_overlap = person("carers_allowance_pre_overlap", period)
        overlapping = person("carers_allowance_overlapping_benefits", period)
        parts = carers_allowance_weekly_by_part_of_year(person, period, parameters)
        if len(parts) == 1 or not calculated_by_model(
            person, period, carers_allowance_pre_overlap
        ):
            # A pre-overlap award that an input supplies or a reform
            # calculates carries no dates, so the payment doesn't read the
            # stage before it.
            share_paid = 1
        else:
            # The overlap rule works week by week, so in the year the
            # earnings taper starts, the overlapping benefits come off only
            # for the share of the year the person keeps the award in, where
            # both stages before the payment carry the parts of the year.
            candidate = person("carers_allowance_pre_couple_limit", period)
            candidate_share, kept_share = carers_allowance_shares_of_year(
                person, period, parts
            )
            kept = kept_share / where(candidate_share > 0, candidate_share, 1)
            by_parts = carries_parts_of_year(
                person,
                period,
                carers_allowance_pre_couple_limit,
                candidate,
                carers_allowance_annual_award(parts),
            ) & carries_parts_of_year(
                person,
                period,
                carers_allowance_pre_overlap,
                pre_overlap,
                candidate * kept,
            )
            share_paid = where(by_parts, kept_share, 1)
        paid = max_(pre_overlap - share_paid * overlapping, 0)
        # Where an overlapping benefit equals the award, float32 leaves about a
        # thousandth of a pound, which is not a payment; a penny is.
        return where(paid < HALF_PENNY, 0, paid)
