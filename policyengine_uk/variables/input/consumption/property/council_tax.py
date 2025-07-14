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

        original_ct = household("council_tax", 2022)

        household_pop_rates = [
            23.863,
            24.036,
            24.207,
            24.372,
            24.537,
            24.706,
            24.873,
            25.035,
        ]  # England=>UK for now, https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationprojections/bulletins/householdprojectionsforengland/2018based

        years = list(range(2022, 2030))
        england_ct_receipts = [36.3, 38.3, 41.2, 43.5, 45.8, 48.4, 51.0, 53.7]
        scotland_ct_receipts = [2.7, 2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5]
        wales_ct_receipts = [1.9, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7]

        data_year = 2022
        end_year = period.start.year

        df = pd.DataFrame(
            dict(
                year=years,
                england=england_ct_receipts,
                wales=wales_ct_receipts,
                scotland=scotland_ct_receipts,
                households=household_pop_rates,
            )
        )

        def get_value(variable, year):
            return df[df.year == int(year)][variable].values[0]
        
        def get_per_household_ratio(variable, start_year, end_year):
            start_value = get_value(variable, start_year)
            end_value = get_value(variable, end_year)
            start_pop = get_value("households", start_year)
            end_pop = get_value("households", end_year)

            print(variable, start_year, end_year, start_value, end_value, start_pop, end_pop)

            print((end_value / start_value), (end_pop / start_pop))

            return (end_value / start_value) / (end_pop / start_pop)

        country = household("country", period).decode_to_str()

        return select(
            [
                country == "ENGLAND",
                country == "WALES",
                country == "SCOTLAND",
                True,
            ],
            [
                original_ct * get_per_household_ratio("england", data_year, end_year),
                original_ct * get_per_household_ratio("wales", data_year, end_year),
                original_ct * get_per_household_ratio("scotland", data_year, end_year),
                original_ct,
            ],
        )
