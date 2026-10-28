from policyengine_uk.model_api import *
from policyengine_uk.utils.carers_allowance_taper import (
    carers_allowance_weekly_by_part_of_year,
)
from policyengine_uk.utils.couple_carer_award import limit_carer_benefit_to_one_partner
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
        "Budget 2026 earnings taper starts, the weeks before the taper and "
        "the weeks under it are compared separately, so overlapping benefits "
        "reduce the allowance only in the weeks it is paid. A supplied "
        "carers_allowance_pre_overlap carries no dates, so it is compared "
        "with the whole year's overlapping benefits."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/4",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/12",
    )

    def formula(person, period, parameters):
        overlapping = person("carers_allowance_overlapping_benefits", period)
        if supplied_input(person, "carers_allowance_pre_overlap", period) is not None:
            pre_overlap = person("carers_allowance_pre_overlap", period)
            return max_(pre_overlap - overlapping, 0)
        # The overlap rule works week by week, so each part of a year the
        # earnings taper starts in is reduced on its own award.
        paid = 0
        for share, weekly in carers_allowance_weekly_by_part_of_year(
            person, period, parameters
        ):
            award = limit_carer_benefit_to_one_partner(
                person, period, weekly * WEEKS_IN_YEAR
            )
            # Held at the precision of a stored amount, so that an
            # overlapping benefit equal to the award leaves nothing.
            paid = paid + share * max_(award.astype(np.float32) - overlapping, 0)
        return paid
