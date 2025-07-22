from policyengine_uk.model_api import *


class monthly_domestic_energy_consumption(Variable):
    label = "Monthly domestic energy consumption"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        # From RF "A chilling crisis", p11. Available at https://www.resolutionfoundation.org/app/uploads/2022/08/A-chilling-crisis.pdf
        # This is very approximate but gives us some distribution of seasonal energy consumption at least.
        ENERGY_CONSUMPTION_RATIOS = [
            350,
            350,
            350,
            180,
            180,
            180,
            180,
            180,
            180,
            300,
            300,
            300,
        ]
        consumption_distribution = np.array(ENERGY_CONSUMPTION_RATIOS) / sum(
            ENERGY_CONSUMPTION_RATIOS
        )
        month = period.start.month
        return (
            household("domestic_energy_consumption", period.this_year)
            * consumption_distribution[month - 1]
        )
