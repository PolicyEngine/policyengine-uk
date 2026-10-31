from policyengine_uk.model_api import *


def hb_standard_earnings_disregard(benunit, period):
    """Selected standard amount, including the permitted-work replacement."""
    return benunit("housing_benefit_applied_standard_earnings_disregard", period)


def hb_childcare_earnings_limit(
    benunit, period, accommodation=None, wtc_disregard=None
):
    """Remaining earnings and tax credits, without an additional-disregard loop.
    By default the accommodation and WTC disregards are the annual variables;
    an accommodation segment passes its own."""
    net = max_(benunit("housing_benefit_net_earnings", period), 0)
    standard = hb_standard_earnings_disregard(benunit, period)
    if accommodation is None:
        accommodation = benunit(
            "housing_benefit_specified_or_temporary_accommodation_disregard", period
        )
    accommodation = min_(max_(accommodation, 0), max_(0, net - standard))
    # Reg 40(2) and Sch 5 para 56 disregard WTC before reg 27(1)(c)
    # deducts childcare. Only the remaining WTC/CTC can fund those charges.
    if wtc_disregard is None:
        wtc_disregard = benunit("housing_benefit_wtc_disregard", period)
    credits = max_(benunit("working_tax_credit", period) - wtc_disregard, 0) + max_(
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
        return hb_childcare_earnings_limit(benunit, period)
