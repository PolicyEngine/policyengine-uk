from policyengine_uk.model_api import *


class ebr_energy_bills_credit(Variable):
    label = "Energy bills credit (EBR)"
    documentation = (
        "Calendar-year compatibility wrapper for the monthly Energy Bills Support "
        "Scheme discount."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://assets.publishing.service.gov.uk/media/632c38bf8fa8f53cb3746e74/energy-bills-support-scheme-ministerial-direction.pdf",
        "https://www.gov.uk/government/news/households-across-northern-ireland-to-start-receiving-600-uk-government-energy-support",
    )

    def formula(household, period, parameters):
        annual_credit = 0
        for month in range(1, MONTHS_IN_YEAR + 1):
            annual_credit = annual_credit + household(
                "monthly_ebr_energy_bills_credit",
                f"{period.this_year}-{month:02d}",
            )
        annual_top_up = parameters(
            period
        ).gov.treasury.energy_bills_rebate.energy_bills_credit
        return annual_credit + annual_top_up
