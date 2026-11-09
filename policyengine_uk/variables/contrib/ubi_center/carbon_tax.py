from policyengine_uk.model_api import *
from policyengine_uk.utils.carbon import published_emissions
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.uk_totals import carried_uk_emissions


class carbon_tax(Variable):
    entity = Household
    label = "Carbon tax"
    documentation = (
        "A tax on the carbon in household consumption. Consumers bear "
        "consumer_incidence of it on their own emissions; the rest falls on "
        "capital, shared by shareholding over the emissions of all UK "
        "households. Those emissions come from the UK spending totals the "
        "data carries (policyengine_uk.utils.uk_totals), or else, in a "
        "simulation built from data, from its weighted total. A household "
        "situation that carries no totals reads the published sector "
        "emissions, which matter only where it sets shareholding."
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
            simulated_emissions = (
                emissions * household("household_weight", period)
            ).sum()
        else:
            simulated_emissions = published_emissions(parameters, period)
        carried = carried_uk_emissions(household, period, parameters)
        total_emissions = where(carried > 0, carried, simulated_emissions)
        consumer_incidence = carbon_tax.consumer_incidence * rate * emissions
        corporate_incidence = (
            (1 - carbon_tax.consumer_incidence) * rate * total_emissions * shareholding
        )
        return consumer_incidence + corporate_incidence
