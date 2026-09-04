from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_category import (
    find_freeze_start,
    time_shift_dataset,
)

warnings.filterwarnings("ignore")


MONTHS_IN_YEAR = 12


def _category_maximum(benunit, period, node_name: str):
    """Per-category national maximum, read at the determination year.

    Frozen rates are held at the level last determined, so the maximum in
    force then is the one that binds, not the current year's.
    """
    lha = benunit.simulation.tax_benefit_system.parameters.gov.dwp.LHA

    if lha.freeze(period):
        determination_period = find_freeze_start(lha.freeze, period.start)[:4]
    else:
        determination_period = str(period.start.year)

    node = getattr(lha, node_name)
    category = benunit("LHA_category", period).decode_to_str()
    caps = {cat: node.children[cat](determination_period) for cat in node.children}
    return pd.Series(category).map(caps).to_numpy(dtype=float)


class uncapped_BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Uncapped LHA rate"
    documentation = "Local Housing Allowance rate before the national maximum"
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
            # Rates are held at the level last determined, so every input to
            # the determination is read at that year, not the current one.
            freeze_start = find_freeze_start(lha.freeze, period.start)
            lha_period = int(freeze_start[:4])  # Get year
        else:
            lha_period = int(period.start.year)

        determination_period = str(lha_period)

        private_rent_index = parameters.gov.indices.private_rent_index
        lha_list_of_rents = time_shift_dataset(
            lha_list_of_rents.copy(), lha_period, private_rent_index
        )

        percentile = lha.percentile(determination_period)

        lha_rates = lha_list_of_rents.groupby(
            ["brma", "lha_category"]
        ).weekly_rent.quantile(percentile)

        # Convert MultiIndex Series to DataFrame for merge
        lha_rates_df = lha_rates.reset_index()
        lha_rates_df.columns = ["brma", "lha_category", "weekly_rent"]

        # Determined rates are rounded to the nearest penny, half up
        # (Schedule 3B paragraph 2(10)); np.round is half-even. Pence are
        # snapped to 6dp first, because an exact half such as 298.835 is
        # held as 29883.499999999996 once scaled and would round down.
        lha_rates_df.weekly_rent = (
            np.floor(np.round(lha_rates_df.weekly_rent * 100, 6) + 0.5) / 100
        )

        lha_lookup_table = pd.DataFrame(
            {
                "brma": brma,
                "lha_category": category,
            }
        )
        # Use merge instead of row-by-row apply for vectorised lookup
        lha_lookup_table = lha_lookup_table.merge(
            lha_rates_df, on=["brma", "lha_category"], how="left"
        )
        return lha_lookup_table.weekly_rent.values * 52


class BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate"
    documentation = "Local Housing Allowance rate, capped at the national maximum"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        """The published Housing Benefit rate.

        Rates are the lower of the Broad Rental Market Area percentile and the
        weekly national maximum for the category (Rent Officers (Housing
        Benefit Functions) Order 1997, Schedule 3B). Universal Credit has its
        own monthly maximum: see ``uc_LHA_cap``.
        """
        rate = benunit("uncapped_BRMA_LHA_rate", period)
        maximum = _category_maximum(benunit, period, "maximum")
        return min_(rate, maximum * 52)


class uc_LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for LHA under Universal Credit"
    documentation = "Rent covered by the Local Housing Allowance for Universal Credit"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        """Universal Credit applies a monthly national maximum.

        The monthly figures in Schedule 1 to the Rent Officers (Universal
        Credit Functions) Order 2013 are set independently of the weekly
        Housing Benefit maxima and are slightly higher, so annualising the
        weekly figure would impose a ceiling below the statutory one.
        """
        rent = benunit("benunit_rent", period)
        rate = benunit("uncapped_BRMA_LHA_rate", period)
        maximum = _category_maximum(benunit, period, "maximum_monthly")
        return min_(rent, min_(rate, maximum * MONTHS_IN_YEAR))
