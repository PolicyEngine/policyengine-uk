from policyengine_uk.model_api import *


class legacy_means_test_deducted_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax deducted in the legacy means tests"
    documentation = (
        "The income tax that Income Support, Housing Benefit, Pension Credit "
        "and council tax reduction deduct for the person: their income tax "
        "before the winter fuel payment charge, less the tax that the income "
        "the tests treat as capital (rent from property, interest and "
        "dividends), and the other Step 7 charges, would bear if nobody had "
        "employed earnings or self-employment income "
        "(legacy_means_test_uncounted_income_tax_without_earnings). The tests "
        "disregard tax only on income they take into account (IS Regs 1987 "
        "Sch 9 para 1; HB Regs 2006 Sch 5 para 1; HB (SPC) Regs 2006 reg "
        "33(12); SPC Regs 2002 reg 17(10)(a)) and deduct the income tax "
        "deducted from earnings (IS Regs 1987 reg 36(3)(a); HB Regs 2006 reg "
        "36(3)(a)). The model has no PAYE codes and no provision says how to "
        "split one liability, so earnings carry the extra tax they cause, "
        "including what they add on savings, dividends and rent and any Step "
        "7 charge they bring in, as Pension Credit measures the tax on "
        "earnings. Without earnings it equals legacy_means_test_income_tax. "
        "It is not floored: where one partner's earnings move a Step 7 "
        "charge or the marriage allowance off the other partner, that "
        "partner's value can be negative, and the claimant's and partner's "
        "values together give the extra tax the earnings cause. Pension "
        "Credit replaces the tax on self-employed profit with notional tax "
        "(pension_credit_income); the other tests deduct this tax as it is."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/36",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/36",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/33",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
    )

    def formula(person, period, parameters):
        return person("income_tax_before_winter_fuel_payment_charge", period) - person(
            "legacy_means_test_uncounted_income_tax_without_earnings", period
        )
