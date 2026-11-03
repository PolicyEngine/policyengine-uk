from policyengine_uk.model_api import *


class gross_taxable_inputs(Variable):
    """The historical input base for post-tax income and UBI phase-outs.

    This is a modelling choice, not a statutory definition of gross income.
    Employment income excludes statutory pay and employment expenses are not
    deducted. Property and trading income retain signed input values; a net
    miscellaneous loss is floored inside
    miscellaneous_income_before_trading_allowance, which is before the
    trading allowance as trading income is.
    """

    value_type = float
    entity = Person
    label = "Gross taxable inputs for household income and basic income phase-outs"
    documentation = (
        "The historical total_income input sum, retained explicitly for "
        "post_tax_income and UBI phase-outs. Includes gross wages, private "
        "pensions, the tax model's social security income, trading and "
        "property income, savings and other investment income, dividends "
        "and non-negative miscellaneous income. Excludes statutory pay, "
        "maintenance and tax-exempt benefits; it is not ITA 2007 s.23 total "
        "income or programme-specific gross income."
    )
    definition_period = YEAR
    unit = GBP

    adds = [
        "employment_income",
        "private_pension_income",
        "social_security_income",
        "self_employment_income",
        "property_income",
        "savings_interest_income",
        "other_investment_income",
        "dividend_income",
        "miscellaneous_income_before_trading_allowance",
    ]
