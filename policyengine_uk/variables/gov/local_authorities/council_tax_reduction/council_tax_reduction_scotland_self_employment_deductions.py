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
        "The income tax and social security contributions that Scotland's "
        "Council Tax Reduction schemes deduct from self-employed earnings in "
        "place of those actually payable: SSI 2012/303 regs 37 and 38, which "
        "SSI 2021/249 reg 51(9) applies at working age where nobody in the "
        "family has Universal Credit, and SSI 2012/319 regs 36 and 37 at "
        "pension age. The formula charges notional income tax at the basic "
        "rate (the Scottish basic rate for a Scottish taxpayer) on the profit "
        "less only the personal allowance; Class 4 contributions at the main "
        "rate on the profit between the lower and upper profits limits, where "
        "Class 4 is payable at all; and, for years before 2024-25, the Class "
        "2 contributions payable, which SI 2024/377 omitted from reg 38(2) "
        "and reg 37(2) on 6 April 2024. The working-age rule names the "
        "personal relief under ITA 2007 s. 35(1); the formula reads it as the "
        "allowance s. 35(2) leaves after the taper, because s. 35(2) reduces "
        "'the allowance under subsection (1)'. The pension-age rule names the "
        "relief under ss. 36 or 37; Finance Act 2014 omitted s. 36, and s. 37 "
        "gives the section 35 amount to a person born before 6 April 1938, "
        "so the formula reads both as the same tapered s. 35 allowance. A "
        "child minder's chargeable income is one-third of the earnings; the "
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
