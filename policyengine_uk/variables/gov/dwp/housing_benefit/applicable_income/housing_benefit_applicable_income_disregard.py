from policyengine_uk.model_api import *


class housing_benefit_applicable_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income disregards"
    documentation = (
        "Sums disregarded from the claimant's and partner's net earnings. "
        "A lone parent has £25 a week, a couple £10 and anyone else £5, "
        "capped at net earnings. The additional earnings disregard of £17.10 "
        "is added where a work condition is met and net earnings at least "
        "equal the other disregards, the childcare charges deducted and "
        "£17.10. A working-age claimant on Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance has all earnings disregarded. The £20 disregards for "
        "disabled people, carers and some part-time occupations are not "
        "modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        net_earnings = benunit("housing_benefit_net_earnings", period)
        # Working age Sch 4 paras 4, 7 and 10; pension age Sch 4 paras 2 and 7.
        weekly_amount = select(
            [benunit("is_lone_parent", period), benunit("is_couple", period)],
            [p.lone_parent, p.couple],
            default=p.single,
        )
        standard = min_(weekly_amount * WEEKS_IN_YEAR, net_earnings)
        # Working age Sch 4 para 17; pension age Sch 4 para 9.
        additional_amount = p.worker * WEEKS_IN_YEAR
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        covers_additional = net_earnings >= standard + childcare + additional_amount
        additional = where(
            benunit(
                "meets_housing_benefit_additional_earnings_disregard_conditions", period
            )
            & covers_additional,
            additional_amount,
            0,
        )
        # Working age Sch 4 para 12 has no pension-age counterpart. Families
        # on Universal Credit cannot receive Housing Benefit in the model.
        on_income_related_benefit = (
            add(benunit, period, ["income_support", "jsa_income", "esa_income"]) > 0
        )
        pension_age = benunit.any(benunit.members("is_SP_age", period))
        all_earnings = on_income_related_benefit & ~pension_age
        return where(all_earnings, net_earnings, standard + additional)
