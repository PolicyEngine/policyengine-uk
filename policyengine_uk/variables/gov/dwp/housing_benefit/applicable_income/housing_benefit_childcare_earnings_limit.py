from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
    hb_runs_no_formula,
)


def hb_standard_earnings_disregard(benunit, period):
    """Selected standard amount, including the permitted-work replacement."""
    return benunit("housing_benefit_applied_standard_earnings_disregard", period)


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


def hb_wtc_disregard(benunit, period, parameters, accommodation, childcare):
    """WTC disregarded under Sch 5 para 56 where the accommodation disregard
    has this full annual amount and Sch 4 para 17(3)(b) counts this
    childcare deduction."""
    p = parameters(period).gov.dwp
    if not p.tax_credits.active:
        return benunit.empty_array()
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


def hb_childcare_wtc_reserve(benunit, period, parameters, accommodation=None):
    """The WTC this limit keeps from childcare for the Sch 5 para 56
    disregard. By default the accommodation disregard has its annual
    segments; an accommodation segment passes its own amount."""
    name = "housing_benefit_wtc_disregard"
    if hb_runs_no_formula(benunit, period, name):
        return benunit(name, period)
    # Sch 4 para 17(3)(b) counts the childcare deduction, which this limit
    # caps, so the limit tests para 17 with the whole capped charge instead.
    # For the deduction the model calculates, the lesser of that charge and
    # this limit, the answer is the same: if earnings cover the other
    # disregards, the whole charge and the additional amount, they cover any
    # smaller deduction; if not, either the deduction is the whole charge, or
    # this limit caps it and it takes at least all the earnings left, so para
    # 17(1) fails whatever credits remain. A replacement formula for the WTC
    # disregard does not reach this limit, since it could read the deduction.
    charge = hb_capped_childcare_charges(benunit, period, parameters)
    if accommodation is not None:
        return hb_wtc_disregard(benunit, period, parameters, accommodation, charge)
    return sum(
        hb_wtc_disregard(benunit, period, parameters, amount, charge) * share
        for amount, share in hb_accommodation_segments(benunit, period, parameters)
    )


def hb_childcare_earnings_limit(benunit, period, parameters, accommodation=None):
    """Remaining earnings and tax credits, without an additional-disregard loop.
    By default the accommodation disregard is the annual variable; an
    accommodation segment passes its own."""
    net = max_(benunit("housing_benefit_net_earnings", period), 0)
    standard = hb_standard_earnings_disregard(benunit, period)
    reserve = hb_childcare_wtc_reserve(benunit, period, parameters, accommodation)
    if accommodation is None:
        accommodation = benunit(
            "housing_benefit_specified_or_temporary_accommodation_disregard", period
        )
    accommodation = min_(max_(accommodation, 0), max_(0, net - standard))
    # Reg 40(2) and Sch 5 para 56 disregard WTC before reg 27(1)(c)
    # deducts childcare. DWP BW2 W2.179-W2.182 lets WTC/CTC in payment, not
    # other income, meet the charges earnings leave; only the WTC left after
    # that disregard counts. Both amounts are benefit-unit payments.
    credits = max_(benunit("working_tax_credit", period) - reserve, 0) + max_(
        benunit("child_tax_credit", period), 0
    )
    return max_(0, net - standard - accommodation) + credits


class housing_benefit_childcare_earnings_limit(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit childcare earnings and tax-credit limit"
    documentation = (
        "Net claimant/partner earnings after the selected standard, permitted-work "
        "and accommodation disregards, plus WTC/CTC payments after the "
        "Schedule 5 paragraph 56 WTC disregard. Unrelated income "
        "cannot meet remaining childcare charges. The additional earnings "
        "disregard is conditional on earnings covering the childcare deduction "
        "as well as that disregard: when it applies the full capped childcare "
        "charge already fits, so this calculation need not depend on it. This "
        "avoids a circular calculation through the childcare deduction. The "
        "WTC this limit keeps back for the paragraph 56 disregard follows the "
        "same idea: the limit tests paragraph 17 with the whole capped charge, "
        "which gives the disregard the model's own deduction leads to, so it "
        "reads neither the deduction nor the housing_benefit_wtc_disregard "
        "formula. A WTC disregard that a dataset, set_input or a scenario "
        "supplies, or that a reform neutralizes, applies instead; a "
        "replacement formula for it does not reach this limit. Where a "
        "dataset, set_input or a reform supplies or replaces the deduction, "
        "the limit still tests the whole charge, and can keep back WTC that "
        "paragraph 56 does not disregard with the deduction in force. The "
        "WTC edge also runs from this limit through "
        "housing_benefit_applied_standard_earnings_disregard, "
        "housing_benefit_special_earnings_disregard and "
        "housing_benefit_special_earnings_disregard_eligible to "
        "working_tax_credit and its disability elements. With fixed earnings, "
        "WTC entitlement "
        "and its components (including the WTC childcare element) do not "
        "read the HB childcare deduction, limit or applicable income, so "
        "neither this edge nor the direct WTC addition creates a cycle. "
        "Earnings are fixed when the simulation has no baseline or the "
        "labour supply income and substitution elasticities are zero, as "
        "they are by default. Labour supply responses can make earnings "
        "depend on benefits, so this note does not cover a reform that "
        "turns them on."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/30",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/24",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/28",
        "https://assets.publishing.service.gov.uk/media/5a7c7cf7ed915d6969f4538d/hbgm-bw2-assessment-of-income.pdf",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/56",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/40",
    )

    def formula(benunit, period, parameters):
        return hb_childcare_earnings_limit(benunit, period, parameters)
