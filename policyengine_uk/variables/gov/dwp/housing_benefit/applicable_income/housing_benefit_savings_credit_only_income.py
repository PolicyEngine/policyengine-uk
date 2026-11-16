from policyengine_uk.model_api import *


class housing_benefit_savings_credit_only_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit income for a savings-credit-only Pension Credit award"
    documentation = (
        "Income for the Housing Benefit means test of a claimant who, or whose "
        "partner, has a Pension Credit award of savings credit only. The "
        "authority takes the Secretary of State's assessment of net income for "
        "that award and modifies it only for the listed items. Modelled: the "
        "savings credit payable is added, and childcare charges and the "
        "higher Housing Benefit earnings disregards are deducted: any excess "
        "of the lone-parent or permitted-work amount over the amount already "
        "disregarded for Pension Credit, and the separate additional 17.10 "
        "pounds. The Secretary of State's figure is "
        "Pension Credit income, which is already after the Pension Credit "
        "earnings disregards (20 pounds for a lone parent, carer, disabled "
        "or blind earner, otherwise 5 pounds single or 10 pounds couple), so "
        "standard amounts already disregarded for Pension Credit are not "
        "deducted again; other special-standard grounds do not independently "
        "modify that assessment. "
        "Childcare charges are deducted as in the general "
        "route, without the work condition or the cap at earnings. Pension "
        "Credit counts spousal maintenance in full, so Housing Benefit's 15 "
        "pound maintenance disregard (where the family includes a child or "
        "young person) is deducted. Housing "
        "Benefit's own income and tariff income rules do not apply to the "
        "Secretary of State's figure, which already counts Pension Credit "
        "deemed income from capital. Not modelled: "
        "the income and capital of a "
        "partner treated as a household member but not in the Pension Credit "
        "assessment, and income of a non-dependant treated as the claimant's. "
        "War pensions (Great Britain: local schemes under section 134(8) of "
        "the Social Security Administration Act 1992; Northern Ireland: war "
        "pension income above £10 disregarded under Schedule 6 paragraph 1) "
        "are taken as wholly disregarded, as in the general route: the war "
        "pension income the Secretary of State counts "
        "(pension_credit_war_pension_income) is removed from the assessment."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/20",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )

    def formula(benunit, period, parameters):
        # SI 2006/214 reg 27(1) and (3) (NI: SR 2006/406 reg 25): the
        # Secretary of State's assessment of net income for the award, less
        # the war pension income it counts: the model takes the authority to
        # disregard war pensions in full under a section 134(8) local scheme,
        # as the general route does (HB/CTB Guidance Manual P2.576 lets it
        # modify the Pension Service's figure for that).
        pension_credit_income = max_(
            0,
            benunit("pension_credit_income", period)
            - benunit("pension_credit_war_pension_income", period),
        )
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
        # higher amounts Housing Benefit allows come off: the excess of
        # the lone-parent (Sch 4 para 2) or permitted-work (para 5A) amount
        # over the existing Pension Credit deduction, plus the separate
        # additional disregard (para 9). Read the shared applied standard
        # before isolating para 9, so replaced or pre-existing disregards
        # are not deducted again. Other special-standard grounds do not
        # independently modify the Pension Credit assessment. This route
        # has no specified-accommodation disregard.
        lone_parent = benunit("is_lone_parent", period)
        permitted = max_(benunit("housing_benefit_permitted_work_disregard", period), 0)
        standard = benunit(
            "housing_benefit_applied_standard_earnings_disregard", period
        )
        additional = max_(
            0, benunit("housing_benefit_applicable_income_disregard", period) - standard
        )
        higher_standard = where(
            lone_parent | (permitted > 0),
            max_(0, standard - benunit("pension_credit_earnings_disregard", period)),
            0,
        )
        # Reg 27(4)(c)(ii): Pension Credit counts spousal maintenance in full
        # (SPC Regs 2002 reg 15(5)(d)), so the higher amount Housing Benefit
        # disregards is all of its Sch 5 para 20 disregard.
        maintenance = benunit("housing_benefit_maintenance_disregard", period)
        disregard = higher_standard + additional + maintenance
        return max_(
            0,
            pension_credit_income + savings_credit_payable - childcare - disregard,
        )
