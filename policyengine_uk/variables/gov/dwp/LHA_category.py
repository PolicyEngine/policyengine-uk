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
    """Finds the first instant in which the LHA freeze was applied. Returns none if this is impossible.

    Args:
        freeze_parameter (Parameter): The LHA freeze parameter.
        period (str): The period to search up to.

    Returns:
        str: The first instant in which the LHA freeze was applied.
    """
    freeze_start = None
    for i in range(len(freeze_parameter.values_list)):
        param = freeze_parameter.values_list[i]
        if param.instant_str > str(period):
            continue
        if (
            i < len(freeze_parameter.values_list) - 1
            and not freeze_parameter.values_list[i + 1].value
        ):
            return param.instant_str
    return None
