from policyengine_uk.model_api import *


def hb_standard_earnings_disregard(benunit, period):
    """Selected standard amount, including the permitted-work replacement."""
    net = max_(benunit("housing_benefit_net_earnings", period), 0)
    standard = benunit("housing_benefit_special_earnings_disregard", period)
    permitted = max_(benunit("housing_benefit_permitted_work_disregard", period), 0)
    return where(
        permitted > 0,
        min_(net, max_(permitted, benunit("is_lone_parent", period) * standard)),
        standard,
    )


def hb_childcare_earnings_limit(benunit, period, accommodation=None):
    """Remaining earnings and tax credits, without an additional-disregard loop."""
    net = max_(benunit("housing_benefit_net_earnings", period), 0)
    standard = hb_standard_earnings_disregard(benunit, period)
    if accommodation is None:
        accommodation = benunit(
            "housing_benefit_specified_or_temporary_accommodation_disregard", period
        )
    accommodation = min_(max_(accommodation, 0), max_(0, net - standard))
    # DWP BW2 W2.179–W2.182 permits the residual against any WTC/CTC in
    # payment, not other income. Both amounts are benefit-unit payments.
    credits = max_(benunit("working_tax_credit", period), 0) + max_(
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
        "and accommodation disregards, plus WTC/CTC payments. Unrelated income "
        "cannot meet remaining childcare charges. The additional earnings "
        "disregard is conditional on earnings covering the childcare deduction "
        "as well as that disregard: when it applies the full capped childcare "
        "charge already fits, so this calculation need not depend on it. This "
        "avoids a circular calculation through the childcare deduction."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/30",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/24",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/28",
        "https://assets.publishing.service.gov.uk/media/5a7c7cf7ed915d6969f4538d/hbgm-bw2-assessment-of-income.pdf",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
    )

    def formula(benunit, period, parameters):
        return hb_childcare_earnings_limit(benunit, period)
