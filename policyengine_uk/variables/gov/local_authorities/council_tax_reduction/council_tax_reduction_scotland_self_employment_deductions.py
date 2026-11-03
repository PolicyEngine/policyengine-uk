from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable


class council_tax_reduction_scotland_self_employment_deductions(Variable):
    value_type = float
    entity = Person
    label = (
        "Notional tax and contributions on self-employed profit, for Scottish "
        "Council Tax Reduction"
    )
    documentation = (
        "The income tax and social security contributions that a Scottish "
        "council deducts from self-employed earnings for Council Tax "
        "Reduction in place of those actually payable: under SSI 2012/303 "
        "regs 37 and 38, which the Scottish Ministers apply in SSI 2021/249 "
        "reg 51(9) at working age where nobody in the family has Universal "
        "Credit, and under SSI 2012/319 regs 36 and 37 at pension age. The "
        "formula charges notional income tax at the basic "
        "rate (the formula reads the Scottish basic rate for a Scottish "
        "taxpayer; both rates are 20%) on the profit "
        "less only the personal allowance; Class 4 contributions at the main "
        "rate on the profit between the lower and upper profits limits, where "
        "Class 4 is payable at all; and, for years before 2024-25, the Class "
        "2 contributions payable, which the Treasury omitted from reg 38(2) "
        "and reg 37(2) from 6 April 2024 (SI 2024/377). At working age, the "
        "Scottish Ministers allow the personal relief under ITA 2007 s. "
        "35(1) (SSI 2012/303 reg 38(1)); the formula reads it as the "
        "allowance left after the taper, because in s. 35(2) Parliament "
        "reduces 'the allowance under subsection (1)'. At pension age, they "
        "allow the relief under ss. 36 or 37 (SSI 2012/319 reg 37(1)). "
        "Parliament omitted s. 36 for 2015-16 and later years and s. 37 for "
        "2016-17 and later years, and each time extended s. 35 to the people "
        "the omitted section had covered (Finance Act 2014 s. 2(4), (5) and "
        "(9); Finance Act 2015 s. 5(4), (5) and (11)). A council that read "
        "reg 37(1) literally would allow no applicant any relief from "
        "2016-17. Where an Act "
        "repeals and re-enacts a provision, Parliament provides that a "
        "reference to it in subordinate legislation reads as a reference to "
        "the provision re-enacted (Interpretation Act 1978 ss. 17(2)(a) and "
        "23(1)). The formula takes each Finance Act as repealing an "
        "age-related allowance and re-enacting it in the extended s. 35, so "
        "it reads the reference as the tapered s. 35 allowance, which s. "
        "35(1) now gives every individual. A child "
        "minder's chargeable income comes to one-third of the earnings; the "
        "model does not identify child minders, so it treats every profit as "
        "chargeable income in full."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/51",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/37",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/38",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/36",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/37",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/35",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/37",
        "https://www.legislation.gov.uk/ukpga/2014/26/section/2",
        "https://www.legislation.gov.uk/ukpga/2015/11/section/5",
        "https://www.legislation.gov.uk/ukpga/1978/30/section/17",
    )

    def formula(person, period, parameters):
        profit = max_(0, person("self_employment_income", period))
        rates = parameters(period).gov.hmrc.income_tax.rates
        # The Scottish basic rate is the band after the starter rate.
        scottish_bands = parameters.gov.hmrc.income_tax.rates.scotland.rates
        scottish_basic_rate = scottish_bands.brackets[1].rate(period.start)
        basic_rate = where(
            person("pays_scottish_income_tax", period),
            scottish_basic_rate,
            rates.uk.rates[0],
        )
        # "less only the personal relief": no blind person's or marriage
        # allowance, and no married couple's allowance.
        notional_tax = basic_rate * max_(
            0, profit - person("personal_allowance", period)
        )
        class_4 = parameters(period).gov.hmrc.national_insurance.class_4
        lower = class_4.contribution_scale.components[1].threshold
        upper = class_4.contribution_scale.components[2].threshold
        notional_class_4 = where(
            person("ni_class_4_liable", period),
            class_4.contribution_scale.components[1].rate
            * min_(max_(0, profit - lower), upper - lower),
            0,
        )
        # Reg 38(2)(a) and reg 37(2)(a) as they stood on 5 April 2024: the
        # Class 2 contributions payable, unless chargeable income does not
        # exceed the threshold of SSCBA 1992 s. 11.
        class_2 = parameters(period).gov.hmrc.national_insurance.class_2
        notional_class_2 = (
            (period.start.year < 2024)
            * person("ni_liable", period)
            * class_2_liable(profit, class_2)
            * class_2.flat_rate
            * class_2_contribution_weeks(period.start.year)
        )
        return where(
            profit > 0,
            notional_tax + notional_class_4 + notional_class_2,
            0,
        )
