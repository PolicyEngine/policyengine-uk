from policyengine_uk.model_api import *


class housing_benefit_applicable_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income disregards"
    documentation = (
        "Sums disregarded from the claimant's and partner's net earnings. "
        "A lone parent has £25 a week, a couple £10 and anyone else £5, "
        "capped at net earnings. From 5 October 2026 the working-age "
        "Regulations add the specified or temporary accommodation disregard "
        "(housing_benefit_specified_or_temporary_accommodation_disregard), "
        "also capped at net earnings. The additional earnings disregard of "
        "£17.10 is added where a work condition is met and net earnings at "
        "least equal the other disregards (including that one), the childcare "
        "charges deducted and £17.10. A family on Universal Credit, Income "
        "Support, income-based Jobseeker's Allowance or income-related "
        "Employment and Support Allowance "
        "(housing_benefit_on_passporting_benefit) has all earnings "
        "disregarded, at any age: the working-age Regulations then apply "
        "(SI 2006/213 reg 5(1)(b)). The "
        "£20 standard disregard uses established qualifying routes or an "
        "explicit full-amount pre-assessment, without reconstructing partial "
        "carer/occupation earnings allocations. The permitted-work "
        "disregard (Sch 4 para 10A), which replaces paras 3 to 10 but not "
        "para 18, is not yet modelled here."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/157/regulation/2",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        net_earnings = benunit("housing_benefit_net_earnings", period)
        # Working age Sch 4 paras 4, 7 and 10; pension age Sch 4 paras 2 and 7.
        standard = benunit("housing_benefit_special_earnings_disregard", period)
        # Working age Sch 4 para 18 (NI Sch 5 para 18), from 5 October 2026:
        # specified or temporary accommodation. It applies alongside paras 3
        # to 10A, none of which excludes it, and takes the earnings they
        # leave.
        accommodation = min_(
            benunit(
                "housing_benefit_specified_or_temporary_accommodation_disregard",
                period,
            ),
            net_earnings - standard,
        )
        # Working age Sch 4 para 17; pension age Sch 4 para 9.
        additional_amount = p.worker * WEEKS_IN_YEAR
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        # "Equal or exceed", compared in pence: net earnings are float32, so
        # exactly £1,149.20 is held as £1,149.19995, and an exact comparison
        # with the total fails at equality. From 5 October 2026 the total
        # includes the para 18 amount (para 17(3)(a), "paragraphs 3 to 10A
        # and 18"); it is zero under the pension-age para 9(3)(a).
        covers_additional = np.round(net_earnings.astype(float), 2) >= np.round(
            (standard + accommodation + childcare + additional_amount).astype(float),
            2,
        )
        additional = where(
            benunit(
                "meets_housing_benefit_additional_earnings_disregard_conditions", period
            )
            & covers_additional,
            additional_amount,
            0,
        )
        # Working age Sch 4 para 12 (NI: SR 2006/405 Sch 5 para 12): "Where a
        # claimant is on universal credit, income support, an income-based
        # jobseeker's allowance or an income-related employment and support
        # allowance, his earnings." The working-age Regulations apply at any
        # age where the claimant or partner is on one of these benefits (SI
        # 2006/213 reg 5(1)(b); SI 2006/214 reg 5(2)), so there is no age
        # condition.
        on_passporting_benefit = benunit(
            "housing_benefit_on_passporting_benefit", period
        )
        return where(
            on_passporting_benefit,
            net_earnings,
            standard + accommodation + additional,
        )
