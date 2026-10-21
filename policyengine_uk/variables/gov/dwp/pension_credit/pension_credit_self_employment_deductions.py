from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable


class pension_credit_self_employment_deductions(Variable):
    value_type = float
    entity = Person
    label = "Notional tax and contributions on self-employed profit, for Pension Credit"
    documentation = (
        "The income tax and social security contributions deducted from "
        "self-employed earnings for Pension Credit (SPC Regs 2002 regs. 17(11) "
        "and 17B; Computation of Earnings Regulations 1996 regs. 13(4) and "
        "14), in place of those actually payable on the profit: a notional "
        "income tax at the basic rate (the Scottish basic rate for a Scottish "
        "taxpayer) on the profit less only the personal reliefs of ITA 2007 "
        "Part 3 Chapters 2, 3 and 3A appropriate to their circumstances; "
        "Class 4 contributions at the main rate on the profit between the "
        "lower and upper profits limits, where Class 4 is payable at all; and "
        "the Class 2 contributions payable, until reg. 14(2)(a) was omitted on "
        "6 April 2024."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17B",
        "https://www.legislation.gov.uk/uksi/1996/2745/regulation/13",
        "https://www.legislation.gov.uk/uksi/1996/2745/regulation/14",
        "https://www.legislation.gov.uk/uksi/1996/2745/regulation/14/2023-04-06",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/11/2023-04-06",
    )

    def formula(person, period, parameters):
        profit = max_(0, person("self_employment_income", period))
        rates = parameters(period).gov.hmrc.income_tax.rates
        # The Scottish basic rate is the band after the starter rate; read the
        # band itself, since the scale at an instant leaves out the starter
        # band before 2018-19.
        scottish_bands = parameters.gov.hmrc.income_tax.rates.scotland.rates
        scottish_basic_rate = scottish_bands.brackets[1].rate(period.start)
        basic_rate = where(
            person("pays_scottish_income_tax", period),
            scottish_basic_rate,
            rates.uk.rates[0],
        )
        # Chapter 2 (personal and blind person's allowances) and Chapter 3A
        # (marriage allowance, which the model deducts from income) relieve
        # income; Chapter 3 (married couple's allowance) reduces the tax.
        reliefs = add(
            person,
            period,
            ["personal_allowance", "blind_persons_allowance", "marriage_allowance"],
        )
        notional_tax = max_(
            0,
            basic_rate * max_(0, profit - reliefs)
            - person("married_couples_allowance_deduction", period),
        )
        class_4 = parameters(period).gov.hmrc.national_insurance.class_4
        lower = class_4.thresholds.lower_profits_limit
        upper = class_4.thresholds.upper_profits_limit
        notional_class_4 = where(
            person("ni_class_4_liable", period),
            class_4.rates.main * min_(max_(0, profit - lower), upper - lower),
            0,
        )
        class_2 = parameters(period).gov.hmrc.national_insurance.class_2
        # CER 14(2)(a), (3), before 6 April 2024: test this employment's
        # chargeable income, not actual NI profits after trading allowance
        # or other employment losses. SSCBA s.11 supplies the rate and
        # age-liability rules. The compulsory rate is nil from 2024-25.
        notional_class_2 = (
            person("ni_liable", period)
            * class_2_liable(profit, class_2)
            * class_2.flat_rate
            * class_2_contribution_weeks(period.start.year)
        )
        return where(
            profit > 0,
            notional_tax + notional_class_4 + notional_class_2,
            0,
        )
