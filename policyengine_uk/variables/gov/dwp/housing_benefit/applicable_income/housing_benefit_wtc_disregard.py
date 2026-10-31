from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
    housing_benefit_applicable_income_childcare_element,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_childcare_earnings_limit import (
    hb_standard_earnings_disregard,
    housing_benefit_childcare_earnings_limit,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
    hb_uses_annual_override,
)


def hb_fixed_childcare_deduction(benunit, period, parameters):
    """The annual childcare deduction where it, or the limit it reads, is
    supplied (by a dataset, set_input or a scenario), neutralized or
    calculated by a formula a reform put in place of the model's. Otherwise
    None: each accommodation segment calculates its own deduction."""
    childcare = housing_benefit_applicable_income_childcare_element
    if hb_uses_annual_override(benunit, period, childcare.__name__, childcare.formula):
        return benunit(childcare.__name__, period)
    limit = housing_benefit_childcare_earnings_limit
    if hb_uses_annual_override(benunit, period, limit.__name__, limit.formula):
        return min_(
            hb_capped_childcare_charges(benunit, period, parameters),
            benunit(limit.__name__, period),
        )
    return None


def hb_covers_additional_disregard(
    benunit, period, parameters, accommodation, childcare
):
    """Sch 4 para 17(1), (3): whether net earnings at least equal the other
    earnings disregards, the childcare deduction and the additional amount,
    compared in pence, including equality at a float32 earnings boundary.
    Capping the accommodation amount at the earnings the standard disregard
    leaves does not change the answer: where the cap binds, those
    disregards take all the earnings, which then cannot also cover the
    additional amount."""
    net = benunit("housing_benefit_net_earnings", period)
    standard = hb_standard_earnings_disregard(benunit, period)
    p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
    additional = p.worker * WEEKS_IN_YEAR
    return np.round(net.astype(float), 2) >= np.round(
        (standard + accommodation + childcare + additional).astype(float), 2
    )


def hb_wtc_disregard(benunit, period, parameters, accommodation):
    """WTC disregarded under Sch 5 para 56 where the accommodation disregard
    has this full annual amount."""
    p = parameters(period).gov.dwp
    if not p.tax_credits.active:
        return benunit.empty_array()
    # Sch 4 para 17(3)(b) counts the childcare charges deductible under reg
    # 27(1)(c), which come from the earnings left and then from the credits
    # this disregard reduces, so that deduction depends on this disregard.
    # Where the model calculates the deduction, the whole capped charge
    # settles para 17 instead. That gives the same answer only for the
    # model's formula, the lesser of the capped charge and the earnings and
    # tax-credit limit: if earnings cover the whole charge and the
    # additional amount, they cover any smaller deduction; if not, either
    # the deduction is the whole charge, or the limit caps it and it takes
    # at least all the earnings left, so para 17 fails whatever credits
    # remain. Where the deduction or its limit is supplied, neutralized or
    # replaced, the two can differ, so the test reads the deduction the
    # earnings disregard reads. A replacement deduction that itself reads
    # the limit depends on this disregard, and the engine stops with a
    # circular-definition error.
    childcare = hb_fixed_childcare_deduction(benunit, period, parameters)
    if childcare is None:
        childcare = hb_capped_childcare_charges(benunit, period, parameters)
    applies = benunit(
        "meets_housing_benefit_additional_earnings_disregard_conditions", period
    ) & ~hb_covers_additional_disregard(
        benunit, period, parameters, accommodation, childcare
    )
    additional = p.housing_benefit.means_test.income_disregard.worker * WEEKS_IN_YEAR
    return where(
        applies,
        min_(max_(benunit("working_tax_credit", period), 0), additional),
        0,
    )


def hb_segment_wtc_disregard(benunit, period, parameters, accommodation):
    """The WTC disregard in one accommodation segment. A supplied,
    neutralized or replaced annual amount applies in every segment."""
    name = "housing_benefit_wtc_disregard"
    if hb_uses_annual_override(
        benunit, period, name, housing_benefit_wtc_disregard.formula
    ):
        return benunit(name, period)
    return hb_wtc_disregard(benunit, period, parameters, accommodation)


class housing_benefit_wtc_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit Working Tax Credit disregard"
    documentation = (
        "Working Tax Credit disregarded before the childcare deduction when "
        "the additional-disregard work conditions hold but earnings cannot "
        "fund the additional earnings disregard. The amount is capped at "
        "WTC received and the statutory additional amount, using its dated "
        "history, including the temporary 2020 increase. The existing "
        "tax-credit active parameter suppresses it from fiscal year 2025. "
        "This is separate from the earnings-only disregard. Where the "
        "childcare deduction or its limit is supplied, neutralized or "
        "replaced, the earnings test reads the same deduction as the "
        "earnings disregard, so the two additional disregards never both "
        "apply. Where the accommodation disregard starts within the fiscal "
        "year, each effective-date segment has its own earnings test, as "
        "the earnings disregard does; this annual amount combines the "
        "segments' disregards, and entitlement deducts each segment's own."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/56",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/40",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/58",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/6/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2020/371/regulation/5",
        "https://www.legislation.gov.uk/nisr/2020/53/regulation/5",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
    )

    def formula(benunit, period, parameters):
        return sum(
            hb_wtc_disregard(benunit, period, parameters, accommodation) * share
            for accommodation, share in hb_accommodation_segments(
                benunit, period, parameters
            )
        )
