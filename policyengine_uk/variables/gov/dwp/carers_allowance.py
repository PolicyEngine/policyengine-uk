from policyengine_uk.model_api import *
from policyengine_uk.utils.carers_allowance_taper import (
    carers_allowance_shares_of_year,
    carers_allowance_weekly_by_part_of_year,
)
from policyengine_uk.utils.supplied_inputs import supplied_input


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance"
    documentation = (
        "Carer's Allowance payable after the overlapping-benefit adjustment: "
        "the allowance is reduced by any other personal benefit that overlaps "
        "with it, such as State Pension, and only the balance is paid. The "
        "comparison is made on annual amounts, which equals the weekly rule "
        "when the overlapping benefit is paid at a constant rate all year. "
        "Where the overlapping benefit is above the carer rate in some weeks "
        "and lower or absent in others, for example when it is paid for part "
        "of the year, the annual comparison pays less than the weekly rule "
        "would; annual inputs carry no dates to do better. In the year the "
        "Budget 2026 earnings taper starts, overlapping benefits come off "
        "only for the share of the year the allowance is paid in. A supplied "
        "carers_allowance_pre_overlap or carers_allowance_pre_couple_limit "
        "carries no dates, so the whole year's overlapping benefits come off "
        "it. Less than a penny for the year is nil."
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
        supplied = any(
            supplied_input(person, name, period) is not None
            for name in (
                "carers_allowance_pre_overlap",
                "carers_allowance_pre_couple_limit",
            )
        )
        if len(parts) == 1 or supplied:
            share_paid = 1
        else:
            # The overlap rule works week by week, so in the year the
            # earnings taper starts, the overlapping benefits come off only
            # for the share of the year the person is paid in.
            candidate_share, kept_share = carers_allowance_shares_of_year(
                person, period, parts
            )
            share_paid = where(candidate_share > 0, kept_share, 1)
        paid = max_(pre_overlap - share_paid * overlapping, 0)
        # Less than a penny for the year is in practice float32 residue where
        # an overlapping benefit equals the award, not a payment.
        return where(paid < 0.01, 0, paid)
