from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_category import (
    find_freeze_start,
    time_shift_dataset,
)

warnings.filterwarnings("ignore")


class BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate"
    documentation = "Local Housing Allowance rate"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        brma = benunit.value_from_first_person(
            benunit.members.household("brma", period).decode_to_str()
        )
        category = benunit("LHA_category", period).decode_to_str()

        from policyengine_uk.parameters.gov.dwp.LHA import lha_list_of_rents

        parameters = benunit.simulation.tax_benefit_system.parameters
        lha = parameters.gov.dwp.LHA

        # We first need to know what time period to collect rents from. If LHA is frozen, we need to look earlier
        # than the current time period.

        frozen = lha.freeze(period)
        if frozen:
            # Find the first year of the current freeze
            freeze_start = find_freeze_start(lha.freeze, period.start)
            lha_period = int(freeze_start[:4])  # Get year
        else:
            lha_period = int(period.start.year)

        private_rent_index = parameters.gov.indices.private_rent_index
        lha_list_of_rents = time_shift_dataset(
            lha_list_of_rents.copy(), lha_period, private_rent_index
        )

        percentile = lha.percentile(period)

        lha_rates = lha_list_of_rents.groupby(
            ["brma", "lha_category"]
        ).weekly_rent.quantile(percentile)

        lha_lookup_table = pd.DataFrame(
            {
                "brma": brma,
                "lha_category": category,
            }
        )
        lha_lookup_table["weekly_rent"] = lha_lookup_table.apply(
            lambda x: lha_rates.loc[x.brma, x.lha_category], axis=1
        )
        return lha_lookup_table.weekly_rent.values * 52
