from policyengine_uk.model_api import *


class housing_benefit_savings_credit_only_income(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Housing Benefit income where the Pension Credit award is savings credit only"
    )
    documentation = (
        "Income for the Housing Benefit means test of a claimant who, or whose "
        "partner, has a Pension Credit award of savings credit only. The "
        "authority takes the Secretary of State's assessment of net income for "
        "that award and modifies it only for the listed items. Modelled: the "
        "savings credit payable is added, and childcare charges and the "
        "higher Housing Benefit earnings disregards are deducted: a lone "
        "parent's 25 pounds over the amount disregarded for Pension Credit, "
        "and the additional 17.10 pounds. The Secretary of State's figure is "
        "Pension Credit income, which is already after the Pension Credit "
        "earnings disregards (20 pounds for a lone parent, carer, disabled "
        "or blind earner, otherwise 5 pounds single or 10 pounds couple), so "
        "Housing Benefit's own 5 and 10 pound amounts are not deducted again. "
        "Childcare charges are deducted as in the general "
        "route, without the work condition or the cap at earnings. Housing "
        "Benefit's own income and tariff income rules do not apply to the "
        "Secretary of State's figure, which already counts Pension Credit "
        "deemed income from capital. Not modelled: the "
        "maintenance disregards (neither income definition counts "
        "maintenance), the exempt work disregard, the income and capital of a "
        "partner treated as a household member but not in the Pension Credit "
        "assessment, income of a non-dependant treated as the claimant's, and "
        "war pensions (Great Britain: local schemes under section 134(8) of "
        "the Social Security Administration Act 1992; Northern Ireland: war "
        "pension income above £10 disregarded under Schedule 6 paragraph 1); "
        "the model has no war pension income."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )

    def formula(benunit, period, parameters):
        # SI 2006/214 reg 27(1) and (3) (NI: SR 2006/406 reg 25): the
        # Secretary of State's assessment of net income for the award.
        pension_credit_income = benunit("pension_credit_income", period)
        # Reg 27(4)(a): the savings credit payable. A savings-credit-only
        # award pays only the savings credit, so this is the Pension Credit
        # paid (under the Pension Credit freeze, the frozen amount).
        savings_credit_payable = benunit("pension_credit", period)
        # Reg 27(4)(b): childcare charges taken into account under reg
        # 30(1)(c), here as the general route deducts them; the reg 31 work
        # condition and the reg 30(1)(c) cap at earnings are not modelled.
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        # Reg 27(4)(c)(i) and (d) (NI: reg 25(4)(c)(i) and (d)): the
        # Secretary of State's figure is after the SPC Regs 2002 Sch VI
        # earnings disregards (pension_credit_earnings_disregard), so only the
        # higher amounts Housing Benefit allows come off: a lone parent's
        # Sch 4 para 2 disregard (25 pounds) over the amount disregarded for
        # Pension Credit, and the additional disregard of Sch 4 para 9(1)
        # (the para 5A exempt work disregard is not modelled). Housing
        # Benefit's other grounds do not replace the Pension Credit ones. This
        # route applies only under the pension-age Regulations, where the
        # disregard is the standard amount (Sch 4 paras 2 and 7) and the
        # additional amount (para 9), with no specified-accommodation amount.
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        net_earnings = benunit("housing_benefit_net_earnings", period)
        lone_parent = benunit("is_lone_parent", period)
        weekly_amount = select(
            [lone_parent, benunit("is_couple", period)],
            [p.lone_parent, p.couple],
            default=p.single,
        )
        standard = min_(weekly_amount * WEEKS_IN_YEAR, net_earnings)
        additional = max_(
            0, benunit("housing_benefit_applicable_income_disregard", period) - standard
        )
        higher_lone_parent = where(
            lone_parent,
            max_(0, standard - benunit("pension_credit_earnings_disregard", period)),
            0,
        )
        disregard = higher_lone_parent + additional
        return max_(
            0,
            pension_credit_income + savings_credit_payable - childcare - disregard,
        )
