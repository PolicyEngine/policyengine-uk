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
        "It is a replacement, not £20 added to £5 or £10, and it is capped at "
        "the claimant's and partner's net earnings. This is the amount before "
        "permitted work: where housing_benefit_permitted_work_disregard is "
        "above zero, housing_benefit_applicable_income_disregard deducts that "
        "amount in place of this one, keeping this amount only for a lone "
        "parent for whom it is higher (SI 2006/213 Sch 4 para 10A(2), SI "
        "2006/214 Sch 4 para 5A(2), SR 2006/405 Sch 5 para 10A(2) and SR "
        "2006/406 Sch 5 para 5A(2))."
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
