from policyengine_uk.model_api import *


class esa_exempt_work_earnings(Variable):
    value_type = float
    entity = Person
    label = "Weekly earnings for the ESA exempt work limits"
    documentation = (
        "A claimant's earnings in a week, which ESA Regs 2008 reg 45(2) and "
        "(4) compare with the exempt work earnings limits. They are worked "
        "out under the rules for calculating earnings for income-related ESA "
        "(DMG 41189; regs 92 to 99): gross employment and self-employment "
        "income, less income tax and National Insurance on it and half of "
        "the person's own pension contributions (regs 96(3) and 98(4)), "
        "divided by 52. The income tax deducted is the tax on earnings taken "
        "as the lowest slice of the person's non-savings income, so tax on a "
        "pension, a taxable benefit, property, savings or dividends never "
        "comes off earnings; that is the reading most favourable to the "
        "claimant, where PAYE on a second job would take tax at the basic "
        "rate. National Insurance is the Class 1 primary, Class 2 and Class "
        "4 contributions. Enter this variable directly for other earnings, "
        "for example where the regulations' averaging periods give a "
        "different figure."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/96",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/98",
        "https://assets.publishing.service.gov.uk/media/689db34d1fedc616bb13399c/dmg-ch-41.pdf",
    )

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        gross = add(person, period, ["employment_income", "self_employment_income"])
        national_insurance = add(
            person, period, ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
        )
        # Income tax on earnings, with earnings as the lowest slice of
        # non-savings income: the part of earned_taxable_income left after
        # the person's other non-savings income (pensions, taxable benefits)
        # is taken off the top. earned_taxable_income is adjusted net income
        # less the incomes and allowances on the exclusions list.
        exclusions = list(income_tax.earned_taxable_income_exclusions)
        excluded_incomes = [
            variable
            for variable in exclusions
            if variable in income_tax.adjusted_net_income_components
        ]
        taxable_earnings_components = [
            variable
            for variable in [
                "taxable_employment_income",
                "taxable_self_employment_income",
            ]
            if variable not in exclusions
        ]
        earnings_in_base = add(person, period, taxable_earnings_components)
        income_in_base = person("adjusted_net_income", period) - add(
            person, period, excluded_incomes
        )
        other_income = max_(0, income_in_base - earnings_in_base)
        taxable_earnings = max_(
            0, person("earned_taxable_income", period) - other_income
        )
        rates = income_tax.rates
        tax_before_reductions = where(
            person("pays_scottish_income_tax", period),
            rates.scotland.rates.calc(taxable_earnings),
            rates.uk.calc(taxable_earnings),
        )
        reductions = add(person, period, income_tax.income_tax_subtractions)
        tax = max_(0, tax_before_reductions - reductions)
        pension = person("pension_contributions", period) / 2
        net = max_(0, gross - national_insurance - tax - pension)
        return net / WEEKS_IN_YEAR
