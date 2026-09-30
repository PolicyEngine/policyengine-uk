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
        "Housing Benefit earnings disregards are deducted. Pension Credit "
        "income in the model disregards no earnings, so deducting the Housing "
        "Benefit disregards gives the result of the Secretary of State's "
        "figure, which is after the Pension Credit disregards, less the higher "
        "Housing Benefit amounts: £25 rather than £20 for a lone parent, and "
        "the additional earnings disregard, which Pension Credit does not have. "
        "Housing Benefit's own income and tariff income rules do not apply to "
        "the Secretary of State's figure, which already counts Pension Credit "
        "deemed income from capital. Not modelled: the maintenance disregards "
        "(neither income definition counts maintenance), the exempt work "
        "disregard, the income of a partner outside the Pension Credit "
        "assessment, income of a non-dependant treated as the claimant's, and "
        "local war pension schemes."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/27",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/25",
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
        # Reg 27(4)(b): childcare charges, deducted as in the general route.
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        # Reg 27(4)(c)(i) and (d): the Housing Benefit earnings disregards
        # (Sch 4 paras 2, 7 and 9(1)). The Secretary of State's figure is
        # after the SPC Regs 2002 Sch VI disregards (£20 for a lone parent,
        # £5 or £10 otherwise), which the model's Pension Credit income does
        # not apply, so deducting the whole Housing Benefit disregard adds
        # back the Pension Credit disregard and the higher Housing Benefit
        # amount together. Reg 27(5) leaves Housing Benefit's own income rules,
        # including tariff income from capital, out of the figure.
        disregard = benunit("housing_benefit_applicable_income_disregard", period)
        return max_(
            0,
            pension_credit_income + savings_credit_payable - childcare - disregard,
        )
