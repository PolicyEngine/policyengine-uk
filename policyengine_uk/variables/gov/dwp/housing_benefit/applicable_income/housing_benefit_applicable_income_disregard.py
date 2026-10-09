from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
    housing_benefit_applicable_income_childcare_element,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_childcare_earnings_limit import (
    hb_childcare_earnings_limit,
    hb_standard_earnings_disregard,
    housing_benefit_childcare_earnings_limit,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
    hb_uses_annual_override,
)


def hb_segment_deductions(benunit, period, parameters, accommodation):
    """Apply childcare/earnings limits to one full accommodation amount."""
    net = max_(benunit("housing_benefit_net_earnings", period), 0)
    standard = hb_standard_earnings_disregard(benunit, period)
    accommodation = min_(max_(accommodation, 0), max_(net - standard, 0))
    childcare_name = "housing_benefit_applicable_income_childcare_element"
    if hb_uses_annual_override(
        benunit,
        period,
        childcare_name,
        housing_benefit_applicable_income_childcare_element.formula,
    ):
        childcare = benunit(childcare_name, period)
    else:
        limit_name = "housing_benefit_childcare_earnings_limit"
        if hb_uses_annual_override(
            benunit,
            period,
            limit_name,
            housing_benefit_childcare_earnings_limit.formula,
        ):
            childcare_limit = benunit(limit_name, period)
        else:
            childcare_limit = hb_childcare_earnings_limit(
                benunit, period, accommodation
            )
        childcare = min_(
            hb_capped_childcare_charges(benunit, period, parameters), childcare_limit
        )
    name = "housing_benefit_applicable_income_disregard"
    if hb_uses_annual_override(
        benunit, period, name, housing_benefit_applicable_income_disregard.formula
    ):
        return benunit(name, period), childcare
    p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
    additional_amount = p.worker * WEEKS_IN_YEAR
    # Compare in pence, including equality at a float32 earnings boundary.
    covers_additional = np.round(net.astype(float), 2) >= np.round(
        (standard + accommodation + childcare + additional_amount).astype(float), 2
    )
    additional = where(
        benunit(
            "meets_housing_benefit_additional_earnings_disregard_conditions", period
        )
        & covers_additional,
        additional_amount,
        0,
    )
    disregard = where(
        benunit("housing_benefit_on_passporting_benefit", period),
        net,
        standard + accommodation + additional,
    )
    return disregard, childcare


class housing_benefit_applicable_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income disregards"
    documentation = (
        "Sums disregarded from the claimant's and partner's net earnings. "
        "A lone parent has £25 a week, a couple £10 and anyone else £5, "
        "capped at net earnings. From 5 October 2026 the working-age "
        "Regulations add the specified or temporary accommodation disregard "
        "(housing_benefit_specified_or_temporary_accommodation_disregard), "
        "also capped at net earnings. The additional earnings disregard of "
        "£17.10 is added where a work condition is met and net earnings at "
        "least equal the other disregards (including that one), the childcare "
        "charges deducted and £17.10. A family on Universal Credit, Income "
        "Support, income-based Jobseeker's Allowance or income-related "
        "Employment and Support Allowance "
        "(housing_benefit_on_passporting_benefit) has all earnings "
        "disregarded, at any age: the working-age Regulations then apply "
        "(SI 2006/213 reg 5(1)(b)). The "
        "£20 standard disregard uses established qualifying routes or an "
        "explicit full-amount pre-assessment, without reconstructing partial "
        "carer/occupation earnings allocations. A pre-assessed permitted-work amount "
        "(housing_benefit_permitted_work_disregard) replaces the ordinary "
        "standard amount, retaining a higher lone-parent disregard. It does "
        "not replace the separate accommodation or additional disregard."
        " The annual result combines the capped deductions calculated with "
        "the full accommodation amount in each effective-date segment. "
        "Entitlement applies its income threshold and taper within those "
        "segments rather than using an averaged disregard as a weekly rule."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/157/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/10A",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/5A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/10A",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5/paragraph/5A",
    )

    def formula(benunit, period, parameters):
        return sum(
            hb_segment_deductions(benunit, period, parameters, accommodation)[0] * share
            for accommodation, share in hb_accommodation_segments(
                benunit, period, parameters
            )
        )
