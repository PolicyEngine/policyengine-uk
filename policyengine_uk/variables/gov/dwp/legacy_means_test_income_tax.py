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
        "reductions (the married couple's allowance, other tax credits and "
        "the residential finance-cost reduction). Most reductions are not "
        "tied to any income: s.27 orders them only to give the greatest "
        "reduction in liability. Two are: foreign tax credit relief reduces "
        "the tax on the income the foreign tax was paid on (Taxation "
        "(International and Other Provisions) Act 2010 ss.18(2) and 36), and "
        "the residential finance-cost reduction is given on at most the "
        "property business's profits, plus any current-year estate amounts "
        "and within the adjusted total income limit (Income Tax (Trading and "
        "Other Income) Act 2005 ss.274A and 274AA). The finance-cost "
        "reduction (property_finance_cost_relief) therefore comes off the tax "
        "on property income first. The model's other_tax_credits input mixes "
        "foreign tax credit relief with other reductions (venture capital "
        "trust, enterprise investment and maintenance relief, among others) "
        "and records no source, so those reductions are shared in proportion "
        "to the Step 4 tax on each kind of income, as a stated convention. A "
        "credit for foreign tax on rent is therefore partly attributed to "
        "counted income, and the tax deducted is too low. Step 7 charges, "
        "such as the High Income "
        "Child Benefit Charge and the pension annual allowance charge (s.30), "
        "are not tax calculated on any of this income and are not deducted. "
        "The result is income_tax less the tax attributed to capital and the "
        "charges, floored at nil, so a supplied income_tax value flows "
        "through; if it differs from the tax the components imply, the "
        "difference falls on the tax on counted income."
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
        "https://www.legislation.gov.uk/ukpga/2010/8/section/18",
        "https://www.legislation.gov.uk/ukpga/2010/8/section/36",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/274A",
        "https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
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
        # Step 6 reductions. The residential finance-cost reduction is relief
        # for the property business's costs, given on at most its profits
        # (ITTOIA 2005 ss.274A-274AA), so it comes off the tax on property
        # income first. The rest have no recorded source and are shared in
        # proportion to the Step 4 tax left.
        reductions = min_(
            add(person, period, p.income_tax_subtractions), before_reductions
        )
        finance_cost_relief = min_(
            person("property_finance_cost_relief", period),
            min_(person("property_income_tax", period), reductions),
        )
        general_reductions = reductions - finance_cost_relief
        capital_after_relief = capital - finance_cost_relief
        tax_after_relief = before_reductions - finance_cost_relief
        capital_share = np.divide(
            capital_after_relief,
            tax_after_relief,
            out=np.zeros_like(capital_after_relief, dtype=float),
            where=tax_after_relief > 0,
        )
        capital_after_reductions = (
            capital_after_relief - general_reductions * capital_share
        )
        # Starting from income tax keeps any supplied income_tax value: the
        # result is the tax on counted income less its share of reductions
        # whenever income tax is calculated.
        return max_(
            0,
            person("income_tax", period) - capital_after_reductions - charges,
        )
