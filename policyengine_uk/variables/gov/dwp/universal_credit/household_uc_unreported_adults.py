from policyengine_uk.model_api import *


class household_uc_unreported_adults(Variable):
    value_type = int
    entity = Household
    label = "Number of adults in benunits without reported UC capital"
    documentation = (
        "Adults counted in the residual household-capital proxy for Universal "
        "Credit, including adults in non-claimant benunits when capital "
        "ownership cannot be identified."
    )
    definition_period = YEAR
    unit = "adult"

    def formula(household, period, parameters):
        person = household.members
        reported_capital = person.benunit("uc_reported_capital", period)
        has_reported_capital = reported_capital >= 0
        is_adult = person("is_adult", period)
        return household.sum(is_adult * ~has_reported_capital)
