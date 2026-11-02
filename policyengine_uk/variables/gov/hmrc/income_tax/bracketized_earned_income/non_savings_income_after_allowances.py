from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax_allocation import non_savings_deductions


class non_savings_income_after_allowances(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax after allowances"
    documentation = (
        "Net income (before the Gift Aid step of adjusted net income, which "
        "does not reduce the income charged to tax) less savings and dividend "
        "income and the reliefs and allowances set against non-savings "
        "income, floored at nil: the income below savings and dividends "
        "(ITA 2007 s. 16) after Steps 2 and 3. The taxpayer sets the reliefs "
        "and allowances against it in the way that gives the least tax (ITA "
        "2007 s. 25(2)), and from 2027-28 against the rest of it before "
        "property income (s. 25(3A)). The allocation computes it from its own "
        "share, without the float32 rounding of a sum that adds the relief "
        "back. property_income_tax, taxable_property_income_after_allowances "
        "and earned_taxable_income read it."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007, s. 16",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
        ),
        dict(
            title="Income Tax Act 2007, s. 25",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        # Not adjusted_net_income: it deducts the grossed-up Gift Aid gift
        # (ITA 2007 s. 58), which raises the rate limits instead
        # (s. 414(2)(b)) and is no deduction from taxable income. The
        # allocation takes net income, adds back the trade loss relief that
        # the share sets against savings and dividends (s. 25), and deducts
        # savings, dividends and the reliefs and allowances the share sets
        # against non-savings income.
        return non_savings_deductions(person, period).non_savings_left
