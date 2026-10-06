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
        is_shared = benunit.any(household("is_shared_accommodation", period.this_year))
        num_adults_in_hh = benunit.max(household.sum(person("is_adult", period)))
        eldest_adult_age_in_hh = benunit.max(household.max(person("age", period)))
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


def find_freeze_anchor(freeze_parameter: Parameter, period: str) -> str:
    """Finds the instant whose rents a frozen LHA rate should be based on.

    Frozen rates are held in cash terms at the level set in the most recent
    year in which LHA was *not* frozen, so this returns 1 January of the
    latest fiscal year, up to the given period, in which the freeze
    parameter is false.

    It reads the parameter a year at a time rather than walking its stored
    values. Fiscal-year conversion stores a value only where a year changes,
    so a run of unfrozen years can be one stored value dated at its start,
    and the latest stored false value would give the run's first year rather
    than its last.

    Args:
        freeze_parameter (Parameter): The LHA freeze parameter.
        period (str): The period to search up to.

    Returns:
        str: 1 January of the latest unfrozen year, or None if not frozen.
    """
    if not freeze_parameter.values_list or not freeze_parameter(period):
        # Not currently frozen.
        return None

    # 30 April reads the fiscal year, which is the whole calendar year's
    # value once converted.
    first_year = int(freeze_parameter.values_list[-1].instant_str[:4])
    for year in range(int(str(period)[:4]), first_year - 1, -1):
        if not freeze_parameter(f"{year}-04-30"):
            return f"{year}-01-01"

    # Frozen for the whole of the parameter's history; fall back to the
    # oldest value available.
    return freeze_parameter.values_list[-1].instant_str


# Universal Credit's monthly national maximum is only modelled from April
# 2020. No monthly maximum existed in 2016, and the 2017 to 2019 figures were
# targeted affordability caps applying to listed areas rather than nationally.
# Parameters are backdated to 2015 on load, so the series has to be gated
# here: omitting the early YAML entries does not stop the lookup returning
# the 2020 figure for earlier years.
MONTHLY_MAXIMUM_FIRST_YEAR = 2020


def category_maximum(benunit, period, node_name: str):
    """Per-category national maximum, read at the determination year.

    Frozen rates are held at the level last determined, so the maximum in
    force then is the one that binds, not the current year's.
    """
    lha = benunit.simulation.tax_benefit_system.parameters.gov.dwp.LHA

    if lha.freeze(period):
        determination_period = find_freeze_anchor(lha.freeze, period.start)[:4]
    else:
        determination_period = str(period.start.year)

    node = getattr(lha, node_name)
    category = benunit("LHA_category", period).decode_to_str()
    caps = {cat: node.children[cat](determination_period) for cat in node.children}
    return pd.Series(category).map(caps).to_numpy(dtype=float)
