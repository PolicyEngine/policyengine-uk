from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class carbon_tax(Variable):
    entity = Household
    label = "Carbon tax"
    documentation = (
        "A tax on the carbon in household consumption. Consumers bear "
        "consumer_incidence of it on their own emissions; the rest falls on "
        "capital, shared by shareholding over the emissions of all UK "
        "households. In a simulation built from data those emissions are the "
        "weighted total; a household situation reads the published sector "
        "totals carbon_consumption is built from, which matter only where "
        "the situation sets shareholding."
    )
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        carbon_tax = parameters(period).gov.contrib.ubi_center.carbon_tax
        rate = carbon_tax.rate
        emissions = household("carbon_consumption", period)
        # Household's share of total stocks and other corporate tax exposure.
        shareholding = household("shareholding", period)
        if built_from_data(household.simulation):
            total_emissions = (emissions * household("household_weight", period)).sum()
        else:
            categories = household.simulation.tax_benefit_system.get_variable(
                "consumption"
            ).adds
            sector_emissions = parameters(period).household.consumption.carbon.emissions
            total_emissions = sum(
                sector_emissions[category.replace("_consumption", "")]
                for category in categories
            )
        consumer_incidence = carbon_tax.consumer_incidence * rate * emissions
        corporate_incidence = (
            (1 - carbon_tax.consumer_incidence) * rate * total_emissions * shareholding
        )
        return consumer_incidence + corporate_incidence
