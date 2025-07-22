from policyengine_uk.model_api import *


class council_tax(Variable):
    value_type = float
    entity = Household
    label = "Council Tax"
    documentation: str = "Gross amount spent on Council Tax, before discounts"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        if period.start.year < 2023:
            # We don't have growth rates for council tax by nation before this.
            return 0

        if household.simulation.dataset is None:
            return 0

        data_year = household.simulation.dataset.time_period

        original_ct = household("council_tax", data_year)

        ct = parameters.gov.economic_assumptions.indices.obr.council_tax

        def get_growth(country):
            param = getattr(ct, country)
            return param(period.start.year) / param(data_year)

        country = household("country", period).decode_to_str()

        return select(
            [
                country == "ENGLAND",
                country == "WALES",
                country == "SCOTLAND",
                True,
            ],
            [
                original_ct * get_growth("england"),
                original_ct * get_growth("wales"),
                original_ct * get_growth("scotland"),
                original_ct,
            ],
        )
