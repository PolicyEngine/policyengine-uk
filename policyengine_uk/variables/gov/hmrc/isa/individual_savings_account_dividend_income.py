from policyengine_uk.model_api import *


class individual_savings_account_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Dividends and distributions from ISAs"
    documentation = "Annual dividends and distributions from Individual Savings Accounts, separate from ordinary dividend income and ISA interest. Exclude principal withdrawals, capital gains and unrealised appreciation. The model counts this amount once as market income and excludes it from taxable dividends."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/22"
