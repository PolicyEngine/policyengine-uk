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
        "income in the model disregards no earnings, whereas the Secretary of "
        "State's figure is after the Pension Credit disregards (£20 for a lone "
        "parent, £5 single or £10 couple otherwise). Deducting the Housing "
        "Benefit disregards (£25 for a lone parent, £5 or £10 otherwise, and "
        "the additional £17.10) therefore gives that figure less the higher "
        "Housing Benefit amounts the regulation allows: £5 more for a lone "
        "parent, and the additional disregard. This holds while neither "
        "programme's £20 disregards for disabled people, carers and some "
        "occupations are modelled; for those earners the Secretary of State's "
        "figure is after £20, so the omission changes the income assessed, the "
        "savings credit payable and possibly whether the award is savings "
        "credit only. Childcare charges are deducted as in the general "
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
        # Reg 27(4)(c)(i) (Sch 4 para 2: £25 for a lone parent, against SPC
        # Regs 2002 Sch VI para 1's £20) and (d) (Sch 4 para 9(1), the
        # additional £17.10; the para 5A exempt work disregard is not
        # modelled). NI: reg 25(4)(c)(i) and (d), Sch 5 paras 2 and 9(1).
        # The model's Pension Credit income applies no Sch VI disregard, so
        # deducting the whole Housing Benefit disregard also takes off the Sch
        # VI amounts already inside the Secretary of State's figure: £20 for a
        # lone parent (para 1) and £5 or £10 otherwise (para 5), which match
        # Sch 4 paras 2 and 7 but for the lone parent's extra £5. Neither
        # schedule's £20 disregards (Sch VI paras 2 to 4; Sch 4 paras 3 to 5)
        # are modelled. If Sch 4 paras 3 to 5 are added to the disregard
        # variable, this route needs the Sch VI grounds instead, as reg 27(4)
        # does not let Housing Benefit's own £20 grounds replace them.
        # Reg 27(5): Housing Benefit's own income rules, including tariff
        # income from capital, do not apply to the Secretary of State's figure.
        disregard = benunit("housing_benefit_applicable_income_disregard", period)
        return max_(
            0,
            pension_credit_income + savings_credit_payable - childcare - disregard,
        )
