from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.treasury.energy_bills_rebate.monthly_ebr_energy_bills_credit import (
    ebss_credit,
)


class hbai_energy_bills_rebate(Variable):
    label = "Energy Bills Rebate in HBAI income"
    documentation = (
        "The Energy Bills Rebate by financial year, as HBAI counts it: the "
        "Council Tax Rebate and the Energy Bills Support Scheme credit paid "
        "from April of the year to the next March. HBAI counts the whole "
        "October 2022 to March 2023 credit in FYE 2023. energy_bills_rebate "
        "sums the credit by calendar year instead. The household's nation "
        "is the financial year's, so the January to March instalments follow "
        "the scheme of the year they belong to."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2023/households-below-average-income-series-quality-and-methodology-information-report-fye-2023"

    def formula(household, period, parameters):
        country = household("country", period)
        credit = 0
        # April of the year to March of the next.
        for months_after_january in range(3, 15):
            month = period.first_month.offset(months_after_january, MONTH)
            eligible = household("ebr_energy_bills_credit_eligible", month)
            credit = credit + eligible * ebss_credit(parameters, month, country)
        annual_top_up = parameters(
            period
        ).gov.treasury.energy_bills_rebate.energy_bills_credit
        return household("ebr_council_tax_rebate", period) + credit + annual_top_up
