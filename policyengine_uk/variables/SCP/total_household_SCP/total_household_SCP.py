from policyengine_uk.model_api import *

class total_household_scp(Variable):
    entity = Household
    label = "Total household SCP"
    definition_period = WEEK
    value_type = float
    unit = GBP


    def formula(household, period):
        # Access the individual SCP variable for each member of the household
        individual_scp = household.members("individual", period)
        # Sum up the individual SCP values to get the total household SCP
        return household.sum(individual_scp)
