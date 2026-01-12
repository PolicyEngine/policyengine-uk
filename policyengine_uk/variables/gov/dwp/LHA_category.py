from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


class LHACategory(Enum):
    A = "Shared accommodation"
    B = "One bedroom"
    C = "Two bedrooms"
    D = "Three bedrooms"
    E = "Four or more bedrooms"


class LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = "LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms"
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C

    def formula(benunit, period, parameters):
        num_rooms = benunit("LHA_allowed_bedrooms", period.this_year)
        person = benunit.members
        household = person.household
        is_shared = benunit.any(
            household("is_shared_accommodation", period.this_year)
        )
        num_adults_in_hh = benunit.max(
            household.sum(person("is_adult", period))
        )
        eldest_adult_age_in_hh = benunit.max(
            household.max(person("age", period))
        )
        has_children = benunit.any(person("is_child", period))
        # Households with only one adult, if under age threshold, can only
        # claim shared if without children:
        # https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28
        p = parameters(period).gov.dwp.LHA
        can_only_claim_shared = (
            (num_adults_in_hh == 1)
            & (eldest_adult_age_in_hh < p.shared_accommodation_age_threshold)
            & ~has_children
        )
        return select(
            [
                is_shared | can_only_claim_shared,
                num_rooms == 1,
                num_rooms == 2,
                num_rooms == 3,
                num_rooms > 3,
            ],
            [
                LHACategory.A,
                LHACategory.B,
                LHACategory.C,
                LHACategory.D,
                LHACategory.E,
            ],
        )


def time_shift_dataset(
    df: pd.DataFrame, year: int, private_rent_index: Parameter
) -> pd.DataFrame:
    """Check if we have rows of data for the given year. If so, remove all other years. If not, select the latest year rows and uprate using the private rent index.

    Args:
        df (pd.DataFrame): The List of Rents.
        year (int): The requests year.
        private_rent_index (Parameter): The private rent index.

    Returns:
        pd.DataFrame: The List of Rents for the given year.
    """
    year = int(year)
    df.year = df.year.astype(int)
    if year in df.year.unique():
        df = df[df.year == year]
    else:
        df = df[df.year == df.year.max()]
        start_instant = f"{df.year.max()}-01-01"
        end_instant = f"{year}-01-01"
        start_index = private_rent_index(start_instant)
        end_index = private_rent_index(end_instant)
        uprating_index = end_index / start_index
        df.weekly_rent = np.round(df.weekly_rent * uprating_index, 2)
        df.year = year
    return df


def find_freeze_start(freeze_parameter: Parameter, period: str) -> str:
    """Finds the start instant of the current freeze period containing the given period.

    The function works backwards from the given period to find when the current freeze
    started. It looks for the most recent transition from false->true (unfreeze->freeze).

    Args:
        freeze_parameter (Parameter): The LHA freeze parameter.
        period (str): The period to search up to.

    Returns:
        str: The instant when the current freeze period started, or None if not frozen.
    """
    # Get all parameter values that are <= the requested period
    values_list = freeze_parameter.values_list
    relevant_values = [v for v in values_list if v.instant_str <= str(period)]

    if not relevant_values:
        return None

    # Check if the period is currently frozen
    # relevant_values is in reverse chronological order (newest first)
    current_state = relevant_values[0].value

    if not current_state:
        # Not currently frozen
        return None

    # Work from most recent backwards to find when this freeze started
    # List is in reverse chronological order: [newest...oldest]
    # Example: [('2026', True), ('2025', True), ('2024', False), ('2023', True)]
    # Find the earliest True in the current frozen period
    for i in range(len(relevant_values)):
        current_value = relevant_values[i]

        if current_value.value:  # This is a freeze=True value
            # Check if the chronologically earlier period (i+1) was unfrozen
            if i == len(relevant_values) - 1:
                # This is the oldest value and it's frozen - use it
                return current_value.instant_str
            elif not relevant_values[i + 1].value:
                # The chronologically earlier value was False
                # This is where the freeze period started
                return current_value.instant_str
            # Otherwise the earlier value was also True, so continue backwards

    return None
