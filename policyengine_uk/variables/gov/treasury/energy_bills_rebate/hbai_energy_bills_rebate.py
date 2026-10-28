from policyengine_uk.model_api import *

# The months of the financial year that starts in April of the model year.
FINANCIAL_YEAR_MONTHS = [(0, month) for month in range(4, 13)] + [
    (1, month) for month in range(1, 4)
]


class hbai_energy_bills_rebate(Variable):
    label = "Energy Bills Rebate in HBAI income"
    documentation = (
        "The Energy Bills Rebate by financial year, as HBAI counts it: the "
        "Council Tax Rebate and the Energy Bills Support Scheme credit paid "
        "from April of the year to the next March. HBAI counts the whole "
        "October 2022 to March 2023 credit in FYE 2023. energy_bills_rebate "
        "sums the credit by calendar year instead."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2023/households-below-average-income-series-quality-and-methodology-information-report-fye-2023"

    def formula(household, period, parameters):
        credit = 0
        for years_ahead, month in FINANCIAL_YEAR_MONTHS:
            credit = credit + household(
                "monthly_ebr_energy_bills_credit",
                f"{period.start.year + years_ahead}-{month:02d}",
            )
        annual_top_up = parameters(
            period
        ).gov.treasury.energy_bills_rebate.energy_bills_credit
        return household("ebr_council_tax_rebate", period) + credit + annual_top_up
