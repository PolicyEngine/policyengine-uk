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
        # of any trade". Neither says how to split a person's tax when they
        # also have other income. Earnings are taken as the lowest slice of
        # their non-savings income, after the allowances they actually have:
        # savings and dividends sit above earnings and other non-savings
        # income (as in ITA 2007 s. 16), property income above the rest of
        # it (as in s. 16A from 2027-28), and other non-savings income
        # (private pensions, State Pension, taxable benefits) above
        # earnings. So tax on other income never comes off earnings. Under RTI, DWP deducts the PAYE
        # actually taken on the job, which can include tax on a State
        # Pension coded against it; that is not modelled.
        p = parameters(period)
        income_tax = p.gov.hmrc.income_tax
        # earned_taxable_income is adjusted net income less the incomes and
        # allowances on the exclusions list. Read that list, so a reform
        # that changes it (for example one that exempts pensions) is
        # followed here.
        exclusions = list(income_tax.earned_taxable_income_exclusions)
        excluded_incomes = [
            variable
            for variable in exclusions
            if variable in income_tax.adjusted_net_income_components
        ]
        earnings_components = [
            "taxable_employment_income",
            "taxable_self_employment_income",
            "taxable_miscellaneous_income",
        ]
        # Match the gross earnings in uc_individual_earned_income_before_mif.
        bi = p.gov.contrib.ubi_center.basic_income.interactions
        if bi.include_in_means_tests and bi.include_in_taxable_income:
            earnings_components.append("basic_income")
        earnings = add(
            person,
            period,
            [
                variable
                for variable in earnings_components
                if variable not in exclusions
            ],
        )
        # The income left in earned_taxable_income before allowances. The
        # part of it above earnings is the person's other non-savings income.
        income_in_base = person("adjusted_net_income", period) - add(
            person, period, excluded_incomes
        )
        other_income = max_(0, income_in_base - earnings)
        taxable_earnings = max_(
            0, person("earned_taxable_income", period) - other_income
        )
        rates = income_tax.rates
        tax = where(
            person("pays_scottish_income_tax", period),
            rates.scotland.rates.calc(taxable_earnings),
            rates.uk.calc(taxable_earnings),
        )
        # Tax reductions (for example the married couple's allowance) come
        # off the tax on earnings first, as allowances do. So the deduction
        # never exceeds the income tax the person pays, never includes a
        # charge such as the High Income Child Benefit Charge, and does not
        # move when other income absorbs more or less of a reduction.
        reductions = add(person, period, income_tax.income_tax_subtractions)
        return max_(0, tax - reductions)
