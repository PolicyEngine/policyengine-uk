from openfisca_uk.model_api import *


class energy_bills_rebate(Variable):
    label = "Energy Bills Rebate"
    documentation = "Amount paid under the Energy Bills Rebate scheme."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return add(
            household,
            period,
            ["ebr_council_tax_rebate", "ebr_energy_bills_credit"],
        )
