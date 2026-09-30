from policyengine_uk.model_api import *


class uc_income_tax_on_earnings(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit deduction for income tax on the person's earnings"
    documentation = (
        "Income tax the person pays in respect of their own employment and "
        "self-employment, which Universal Credit deducts from their earned "
        "income. Tax on pensions, State Pension, property, savings and "
        "dividends is not deducted, nor is the High Income Child Benefit "
        "Charge or the pension annual allowance charge."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2), step 3",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Income Tax Act 2007 s. 16",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
        ),
    ]

    def formula(person, period, parameters):
        # Reg. 55(5)(b) deducts income tax paid by the person "in respect of
        # the employment" and reg. 57(2) step 3 income tax paid "in respect
        # of any trade". When the person has other income too, earnings are
        # taken as the lowest slice of their non-savings income, after the
        # allowances they actually have. Savings and dividends sit above all
        # non-savings income (ITA 2007 s. 16) and property income above the
        # rest of it, so tax on them never falls on earnings. Other
        # non-savings income (private pensions, State Pension, taxable
        # benefits) sits above earnings. This is the tax a standard tax code
        # deducts from a sole or main employment.
        p = parameters(period)
        earnings_components = [
            "taxable_employment_income",
            "taxable_self_employment_income",
            "taxable_miscellaneous_income",
        ]
        # Match the gross earnings in uc_mif_capped_earned_income.
        bi = p.gov.contrib.ubi_center.basic_income.interactions
        if bi.include_in_means_tests and bi.include_in_taxable_income:
            earnings_components.append("basic_income")
        earnings = add(person, period, earnings_components)
        # earned_taxable_income is non-savings, non-property income after
        # allowances. The part of it above earnings belongs to the person's
        # other non-savings income.
        non_savings_non_property_income = person(
            "adjusted_net_income", period
        ) - add(
            person,
            period,
            [
                "taxable_savings_interest_income",
                "taxable_dividend_income",
                "taxable_property_income",
            ],
        )
        other_income = max_(0, non_savings_non_property_income - earnings)
        taxable_earnings = max_(
            0, person("earned_taxable_income", period) - other_income
        )
        rates = p.gov.hmrc.income_tax.rates
        tax = where(
            person("pays_scottish_income_tax", period),
            rates.scotland.rates.calc(taxable_earnings),
            rates.uk.calc(taxable_earnings),
        )
        # Tax reductions (for example the married couple's allowance) can
        # leave total income tax below the tax on the earnings slice; never
        # deduct more than the person pays.
        return min_(tax, person("income_tax", period))
