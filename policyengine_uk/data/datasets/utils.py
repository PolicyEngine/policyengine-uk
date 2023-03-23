import pandas as pd
from typing import List, Dict
import numpy as np
from policyengine_core.data import Dataset
import pickle
from pathlib import Path

STORAGE_FOLDER = Path(__file__).parent.parent / "storage"


def sum_to_entity(
    values: pd.Series, foreign_key: pd.Series, primary_key
) -> pd.Series:
    """Sums values by joining foreign and primary keys.

    Args:
        values (pd.Series): The values in the non-entity table.
        foreign_key (pd.Series): E.g. pension.person_id.
        primary_key ([type]): E.g. person.index.

    Returns:
        pd.Series: A value for each person.
    """
    return values.groupby(foreign_key).sum().reindex(primary_key).fillna(0)


def categorical(
    values: pd.Series, default: int, left: list, right: list
) -> pd.Series:
    """Maps a categorical input to an output using given left and right arrays.

    Args:
        values (pd.Series): The input values.
        default (int): A default value (to replace NaNs).
        left (list): The left side of the map.
        right (list): The right side of the map.

    Returns:
        pd.Series: The mapped values.
    """
    return values.fillna(default).map({i: j for i, j in zip(left, right)})


def sum_from_positive_fields(
    table: pd.DataFrame, fields: List[str]
) -> np.array:
    """Sum from fields in table, ignoring negative values.

    Args:
        table (DataFrame)
        fields (List[str])

    Returns:
        np.array
    """
    return np.where(
        table[fields].sum(axis=1) > 0, table[fields].sum(axis=1), 0
    )


def sum_positive_variables(variables: List[str]) -> np.array:
    """Sum positive variables.

    Args:
        variables (List[str])

    Returns:
        np.array
    """
    return sum([np.where(variable > 0, variable, 0) for variable in variables])


def fill_with_mean(
    table: pd.DataFrame, code: str, amount: str, multiplier: float = 52
) -> np.array:
    """Fills missing values in a table with the mean of the column.

    Args:
        table (DataFrame): Table to fill.
        code (str): Column signifying existence.
        amount (str): Column with values.
        multiplier (float): Multiplier to apply to amount.

    Returns:
        np.array: Filled values.
    """
    needs_fill = (table[code] == 1) & (table[amount] < 0)
    has_value = (table[code] == 1) & (table[amount] >= 0)
    fill_mean = table[amount][has_value].mean()
    filled_values = np.where(needs_fill, fill_mean, table[amount])
    return np.maximum(filled_values, 0) * multiplier
