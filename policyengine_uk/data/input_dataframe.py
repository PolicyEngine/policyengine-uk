"""Turn a DataFrame of simulation inputs into UK dataset tables.

The DataFrame has one row per person and a column for each input and period,
named ``variable__period``. ``Simulation.to_input_dataframe`` exports this
format. A benefit unit or household value sits on the row of each member.

Each person's benefit unit and household come from the ``benunit_id`` and
``household_id`` columns. ``person_benunit_id`` and ``person_household_id``
give them when those columns are absent, and a frame with neither puts each
person in a group of their own. The model stores the two ``person_`` variables
as 32-bit floats, which round identifiers above 2**24
(PolicyEngine/policyengine-uk#2267), so an exported frame can hold them
rounded. The group's own identifier is stored as an integer and is exact.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from policyengine_core.periods import period as period_

from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)

if TYPE_CHECKING:
    from policyengine_core.taxbenefitsystems import TaxBenefitSystem

COLUMN_SEPARATOR = "__"
GROUP_ENTITIES = ("benunit", "household")
# The identifier columns of the dataset tables. The tables take them from the
# people, benefit units and households the frame describes, not from each
# period's own copy.
IDENTIFIER_VARIABLES = frozenset(
    {"person_id"}
    | {f"{group}_id" for group in GROUP_ENTITIES}
    | {f"person_{group}_id" for group in GROUP_ENTITIES}
)
# A 32-bit float smaller than this in size stands for one whole number. From
# this size on, neighbouring whole numbers round to the same float: 2**24 + 1
# rounds to 2**24.
FLOAT32_EXACT_LIMIT = 2**24

# The variable and the period each column is named for, by column.
Columns = Dict[object, Tuple[str, str]]
# A value to set for a period that is not one whole year: its variable, the
# period as the column named it, and one value per member of its entity.
OtherInput = Tuple[str, str, np.ndarray]


def split_column(column) -> Tuple[str, str]:
    """The variable and the period that ``column`` is named for."""
    variable, separator, period = str(column).partition(COLUMN_SEPARATOR)
    if not (variable and separator and period):
        raise ValueError(
            f"Column {column!r} is not named 'variable{COLUMN_SEPARATOR}period', "
            f"such as 'age{COLUMN_SEPARATOR}2025'."
        )
    return variable, period


def _identifier(
    df: pd.DataFrame, columns: Columns, variable: str
) -> Optional[pd.Series]:
    """The column of the identifier ``variable``, or None if the frame has
    none. A simulation holds one set of people and groups, so the columns for
    different periods must agree."""
    named = [column for column, (name, _) in columns.items() if name == variable]
    if not named:
        return None
    identifiers = df[named[0]]
    if identifiers.isna().any():
        raise ValueError(f"Column {named[0]!r} has missing identifiers.")
    for other in named[1:]:
        if not np.array_equal(identifiers.to_numpy(), df[other].to_numpy()):
            raise ValueError(
                f"Columns {named[0]!r} and {other!r} differ. A simulation "
                f"holds the same {variable} values in every period."
            )
    return identifiers


def _group_of_each_person(
    df: pd.DataFrame, columns: Columns, group: str, person_ids: pd.Series
) -> np.ndarray:
    """The identifier of each person's ``group`` (benefit unit or household)."""
    own = _identifier(df, columns, f"{group}_id")
    membership = _identifier(df, columns, f"person_{group}_id")
    source = next(
        identifiers
        for identifiers in (own, membership, person_ids)
        if identifiers is not None
    )
    groups = source.to_numpy()
    if _rounded(groups):
        raise ValueError(
            f"Column {source.name!r} holds identifiers of {FLOAT32_EXACT_LIMIT:,} "
            "or more as 32-bit floats, which cannot tell neighbouring "
            f"identifiers apart, so it cannot say which {group} each person is "
            f"in. Add a '{group}_id' column of integers."
        )
    if own is not None and membership is not None:
        named = membership.to_numpy()
        if named.dtype == np.float32:
            # The model stores person_<group>_id as a 32-bit float, so a frame
            # it exported holds the group's identifier rounded to one.
            differs = groups.astype(np.float32) != named
        else:
            differs = groups != named
        if differs.any():
            row = int(np.flatnonzero(differs)[0])
            raise ValueError(
                f"Columns {own.name!r} and {membership.name!r} put the person "
                f"in row {row} in different groups ({groups[row]} and "
                f"{membership.iloc[row]})."
            )
    return groups


def _rounded(identifiers: np.ndarray) -> bool:
    """Whether 32-bit float ``identifiers`` may each stand for more than one
    whole number."""
    return identifiers.dtype == np.float32 and bool(
        (np.abs(identifiers) >= FLOAT32_EXACT_LIMIT).any()
    )


def _same(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Whether each pair of values is equal, counting two missing values as
    equal."""
    return np.asarray(left == right) | (pd.isna(left) & pd.isna(right))


def dataset_from_input_dataframe(
    df: pd.DataFrame,
    tax_benefit_system: "TaxBenefitSystem",
    default_year: int,
) -> Tuple[UKMultiYearDataset, List[OtherInput]]:
    """The dataset that an input DataFrame describes.

    The dataset holds a year for each whole-year period the frame names (or
    ``default_year`` if it names none), each with the same people, benefit
    units and households. Benefit units and households are in order of their
    identifiers, which is the order ``Simulation.build_from_ids`` gives them.
    Columns that do not name a variable of ``tax_benefit_system`` are left out.

    Args:
        df: One row per person and a column per input, named
            ``variable__period``.
        tax_benefit_system: The model whose variables the columns name.
        default_year: The year to hold the people and groups in when no
            column names a whole year.

    Returns:
        The dataset, and the values the frame gives for periods that are not
        one whole year, which a dataset cannot hold.

    Raises:
        ValueError: If a column is not named ``variable__period``, the frame
            has no ``person_id`` column or repeats a person's identifier, its
            identifier columns contradict each other or hold 32-bit floats
            that may stand for more than one identifier, or the members of a
            benefit unit or household give different values for one of its
            variables.
    """
    if not df.columns.is_unique:
        duplicated = df.columns[df.columns.duplicated()][0]
        raise ValueError(f"Column {duplicated!r} appears more than once.")
    columns = {column: split_column(column) for column in df.columns}

    person_ids = _identifier(df, columns, "person_id")
    if person_ids is None:
        raise ValueError(
            "The DataFrame needs a person_id column, such as "
            f"'person_id{COLUMN_SEPARATOR}{default_year}'."
        )
    if _rounded(person_ids.to_numpy()):
        raise ValueError(
            f"Column {person_ids.name!r} holds identifiers of "
            f"{FLOAT32_EXACT_LIMIT:,} or more as 32-bit floats, which cannot "
            "tell neighbouring identifiers apart. Give them as integers."
        )
    repeated = person_ids[person_ids.duplicated()]
    if len(repeated):
        raise ValueError(
            f"Column {person_ids.name!r} repeats {repeated.iloc[0]}. Each row is "
            "one person with an identifier of their own."
        )
    person_groups, group_ids, first_members, group_indices = {}, {}, {}, {}
    for group in GROUP_ENTITIES:
        person_groups[group] = _group_of_each_person(df, columns, group, person_ids)
        (
            group_ids[group],
            first_members[group],
            group_indices[group],
        ) = np.unique(person_groups[group], return_index=True, return_inverse=True)

    # The columns of each year's person, benefit unit and household tables.
    years: Dict[int, Dict[str, Dict[str, np.ndarray]]] = {}
    other_inputs: List[OtherInput] = []
    for column, (variable, period_text) in columns.items():
        if variable not in tax_benefit_system.variables:
            continue
        period = period_(period_text)
        start = period.start
        whole_year = (
            period.unit == "year"
            and period.size == 1
            and (start.month, start.day) == (1, 1)
        )
        if whole_year:
            year = years.setdefault(
                start.year, {"person": {}, "benunit": {}, "household": {}}
            )
        if variable in IDENTIFIER_VARIABLES:
            continue
        entity = tax_benefit_system.variables[variable].entity.key
        values = df[column].to_numpy()
        if entity in GROUP_ENTITIES:
            group_values = values[first_members[entity]]
            agrees = _same(group_values[group_indices[entity]], values)
            if not agrees.all():
                row = int(np.flatnonzero(~agrees)[0])
                raise ValueError(
                    f"Column {column!r} gives {entity} "
                    f"{person_groups[entity][row]} more than one value. The "
                    "row of each of its members must hold the same value."
                )
            values = group_values
        if whole_year:
            year[entity][variable] = values
        else:
            other_inputs.append((variable, period_text, values))

    if not years:
        years[int(default_year)] = {"person": {}, "benunit": {}, "household": {}}
    datasets = [
        UKSingleYearDataset(
            person=pd.DataFrame(
                {
                    "person_id": person_ids.to_numpy(),
                    "person_benunit_id": person_groups["benunit"],
                    "person_household_id": person_groups["household"],
                    **tables["person"],
                }
            ),
            benunit=pd.DataFrame(
                {"benunit_id": group_ids["benunit"], **tables["benunit"]}
            ),
            household=pd.DataFrame(
                {"household_id": group_ids["household"], **tables["household"]}
            ),
            fiscal_year=fiscal_year,
        )
        for fiscal_year, tables in sorted(years.items())
    ]
    return UKMultiYearDataset(datasets=datasets), other_inputs
