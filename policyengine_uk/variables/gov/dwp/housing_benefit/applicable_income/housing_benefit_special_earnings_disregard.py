from policyengine_uk.model_api import *


class housing_benefit_special_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit selected standard earnings disregard"
    documentation = (
        "Standard disregard selected before the additional/accommodation "
        "amounts: lone-parent precedence, otherwise the special amount for "
        "a qualifying family, otherwise the ordinary couple/single amount. "
        "It is a replacement, not £20 added to £5 or £10. The total standard "
        "deduction is capped at the claimant's and partner's net earnings."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        weekly = select(
            [
                benunit("is_lone_parent", period),
                benunit("housing_benefit_special_earnings_disregard_eligible", period),
                benunit("is_couple", period),
            ],
            [p.lone_parent, p.special, p.couple],
            default=p.single,
        )
        return min_(
            weekly * WEEKS_IN_YEAR, benunit("housing_benefit_net_earnings", period)
        )
