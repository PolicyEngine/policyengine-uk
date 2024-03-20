from policyengine_uk.model_api import *


class carbon_tax(Variable):
    entity = Household
    label = "Carbon tax"
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        carbon_tax = parameters(period).gov.contrib.ubi_center.carbon_tax
        rate = carbon_tax.rate
        emissions = household("carbon_consumption", period)
        # Household's share of total stocks and other corporate tax exposure.
        shareholding = household("shareholding", period)
        total_emissions = (
            emissions * household("household_weight", period)
        ).sum()
        consumer_incidence = carbon_tax.consumer_incidence * rate * emissions
        corporate_incidence = (
            (1 - carbon_tax.consumer_incidence)
            * rate
            * total_emissions
            * shareholding
        )
        return consumer_incidence + corporate_incidence
