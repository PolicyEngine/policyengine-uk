from policyengine_uk.model_api import *


class pension_credit_earnings(Variable):
    label = "Earnings for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17A"

    def formula(benunit, period, parameters):
        # Get the list of earnings sources from parameters
        earnings_sources = parameters(
            period
        ).gov.dwp.pension_credit.income.earnings_sources
        return add(benunit, period, earnings_sources)
