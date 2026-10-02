from policyengine_uk.model_api import *


class legacy_means_test_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax deducted in the legacy means tests"
    documentation = (
        "Income Tax on the income the legacy means tests take into account. The "
        "tests disregard tax only on income they count (Income Support Schedule 9 "
        "paragraph 1; Housing Benefit Schedule 5 paragraph 1; pension-age Housing "
        "Benefit regulation 33(12); Pension Credit regulation 17(10)(a); the "
        "council tax reduction schemes' equivalents), and they treat savings "
        "interest, dividends and property income as capital, not income. So this "
        "is the tax calculated on the person's other income (earned_income_tax, "
        "which covers earnings, pensions and taxable benefits) at Step 4 of "
        "Income Tax Act 2007 s.23, less that income's share of the Step 6 tax "
        "reductions (the married couple's allowance and other tax credits). "
        "Neither tax law nor the benefit regulations say which income a "
        "reduction relieves (s.27 orders reductions only to give the greatest "
        "reduction in liability), so the model shares them in proportion to the "
        "Step 4 tax on each kind of income. Step 7 charges, such as the High "
        "Income Child Benefit Charge and the pension annual allowance charge "
        "(s.30), are not tax calculated on any of this income and are not "
        "deducted."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/33",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/27",
        "https://www.legislation.gov.uk/ukpga/2007/3/section/30",
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax
        # Step 4 tax on the income the means tests count, and on the income
        # they treat as capital.
        counted = person("earned_income_tax", period)
        capital = add(
            person,
            period,
            ["savings_income_tax", "dividend_income_tax", "property_income_tax"],
        )
        before_reductions = counted + capital
        # Step 7 charges: everything income tax adds beyond the Step 4 tax.
        charges = max_(
            0, add(person, period, p.income_tax_additions) - before_reductions
        )
        # Step 6 reductions, shared in proportion to the Step 4 tax.
        reductions = min_(
            add(person, period, p.income_tax_subtractions), before_reductions
        )
        capital_share = np.divide(
            capital,
            before_reductions,
            out=np.zeros_like(capital, dtype=float),
            where=before_reductions > 0,
        )
        capital_after_reductions = capital - reductions * capital_share
        # Starting from income tax keeps any supplied income_tax value: the
        # result is the tax on counted income less its share of reductions
        # whenever income tax is calculated.
        return max_(
            0,
            person("income_tax", period) - capital_after_reductions - charges,
        )
