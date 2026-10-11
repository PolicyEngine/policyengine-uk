"""Turn a DataFrame of simulation inputs into UK dataset tables.

The DataFrame has one row per person and a column for each input and period,
named ``variable__period``. ``Simulation.to_input_dataframe`` exports this
format. A benefit unit or household value sits on the row of each member.

Each person's benefit unit and household come from the ``benunit_id`` and
``household_id`` columns. ``person_benunit_id`` and ``person_household_id``
give them when those columns are absent, and a frame with neither puts each
person in a group of their own. The model stores the two ``person_`` variables
as 32-bit floats, which round identifiers of 2**24 or more
(PolicyEngine/policyengine-uk#2267), so an exported frame can hold them
rounded. The group's own identifier is stored as an integer and is exact.

Identifiers are read as whole numbers, value by value, and a float that may
stand for more than one whole number is refused rather than allowed to merge
two people or groups.

The identifiers hold for every period, and a simulation built from a frame
holds them all as inputs in each whole year a column names.
``Simulation.to_input_dataframe`` gives them for each such year too
(``with_identifiers_in_each_year``), so that an exported frame loads back to
a simulation that exports it again.
"""

import warnings
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

# The variable and the period each column is named for, by column.
Columns = Dict[object, Tuple[str, str]]
# A value to set on the simulation: its variable, the period as the column
# named it, and one value per member of its entity.
Input = Tuple[str, str, np.ndarray]


def exact_limit(dtype) -> Optional[int]:
    """The size from which floats of ``dtype`` stop telling neighbouring whole
    numbers apart, or None if ``dtype`` is not a float type.

    A float smaller than this in size stands for one whole number. From this
    size on, neighbouring whole numbers round to the same float: for 32-bit
    floats the limit is 2**24, and 2**24 + 1 rounds to 2**24.
    """
    dtype = np.dtype(dtype)
    if dtype.kind != "f":
        return None
    return 2 ** (np.finfo(dtype).nmant + 1)


FLOAT32_EXACT_LIMIT = exact_limit(np.float32)
INT64 = np.iinfo(np.int64)


def split_column(column) -> Tuple[str, str]:
    """The variable and the period that ``column`` is named for."""
    variable, separator, period = str(column).partition(COLUMN_SEPARATOR)
    if not (variable and separator and period):
        raise ValueError(
            f"Column {column!r} is not named 'variable{COLUMN_SEPARATOR}period', "
            f"such as 'age{COLUMN_SEPARATOR}2025'."
        )
    return variable, period


def _is_integer(value) -> bool:
    return isinstance(value, (int, np.integer)) and not isinstance(
        value, (bool, np.bool_)
    )


def _is_float(value) -> bool:
    return isinstance(value, (float, np.floating))


def _not_whole(column, value) -> ValueError:
    return ValueError(
        f"Column {column!r} holds {value!r}, which is not a whole number. "
        "Identifiers must be whole numbers."
    )


def _ambiguous(column, dtype) -> ValueError:
    dtype = np.dtype(dtype)
    return ValueError(
        f"Column {column!r} holds identifiers of {exact_limit(dtype):,} or more "
        f"as {8 * dtype.itemsize}-bit floats, which cannot tell neighbouring "
        "identifiers apart. Give identifiers as integers, and name each "
        "person's groups in 'benunit_id' and 'household_id' columns."
    )


def _too_large(column) -> ValueError:
    return ValueError(
        f"Column {column!r} holds identifiers too large for 64-bit integers."
    )


def _whole_number(column, value) -> int:
    """One identifier as an integer, if it stands for one whole number."""
    if _is_integer(value):
        number = int(value)
    elif not _is_float(value):
        raise _not_whole(column, value)
    elif not np.isfinite(value) or value != np.floor(value):
        raise _not_whole(column, value)
    else:
        dtype = np.asarray(value).dtype
        if abs(value) >= exact_limit(dtype):
            raise _ambiguous(column, dtype)
        number = int(value)
    if not INT64.min <= number <= INT64.max:
        raise _too_large(column)
    return number


def _as_integers(identifiers: pd.Series) -> np.ndarray:
    """``identifiers`` as 64-bit integers.

    A column can mix types (an ``object`` column of integers and floats of
    different sizes), so each value is read at its own precision.

    Raises:
        ValueError: If a value is not a whole number, does not fit in 64 bits,
            or is a float that may stand for more than one whole number.
    """
    column = identifiers.name
    values = identifiers.to_numpy()
    if values.dtype.kind == "i":
        return values.astype(np.int64)
    if values.dtype.kind == "u":
        if len(values) and values.max() > INT64.max:
            raise _too_large(column)
        return values.astype(np.int64)
    if values.dtype.kind == "f":
        whole = np.isfinite(values) & (values == np.floor(values))
        if not whole.all():
            raise _not_whole(column, values[~whole][0])
        if (np.abs(values) >= exact_limit(values.dtype)).any():
            raise _ambiguous(column, values.dtype)
        return values.astype(np.int64)
    if values.dtype.kind == "O":
        return np.array([_whole_number(column, value) for value in values], np.int64)
    if len(values):
        raise _not_whole(column, values[0])
    return values.astype(np.int64)


def _float_names(groups: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Whether each float in ``values`` names the matching group: exactly, or
    as the group's identifier rounded to a 32-bit float.

    The model stores ``person_<group>_id`` as a 32-bit float, so a frame it
    exported holds each group's identifier rounded to one. A wider float names
    the group in that way only if it is that 32-bit float, as held or as CSV
    writes it: with the fewest digits that give it back at 32 bits
    (900,000,064 as 900000060.0, a different 64-bit float). Any other float
    that merely rounds to the same 32-bit one names another group.
    """
    exact = groups.astype(values.dtype) == values
    as_float32 = values.astype(np.float32)
    rounded = (groups.astype(np.float32) == as_float32) & ~exact
    held = rounded & (as_float32.astype(values.dtype) == values)
    written = np.zeros(len(values), dtype=bool)
    for index in np.flatnonzero(rounded & ~held):
        written[index] = float(str(as_float32[index])) == values[index]
    return exact | held | written


def _names_group(group: int, value) -> bool:
    """Whether the identifier ``value`` names ``group``."""
    if _is_float(value):
        return bool(_float_names(np.asarray([group]), np.asarray([value]))[0])
    return _is_integer(value) and int(value) == group


def _differs(groups: np.ndarray, named: pd.Series) -> np.ndarray:
    """Whether each identifier in ``named`` names a group other than the one
    ``groups`` gives that person."""
    values = named.to_numpy()
    if values.dtype.kind == "f":
        return ~_float_names(groups, values)
    if values.dtype.kind in "iu":
        return groups != values
    return np.array(
        [not _names_group(group, value) for group, value in zip(groups, values)],
        dtype=bool,
    )


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
    df: pd.DataFrame, columns: Columns, group: str, person_ids: np.ndarray
) -> np.ndarray:
    """The identifier of each person's ``group`` (benefit unit or household)."""
    own = _identifier(df, columns, f"{group}_id")
    membership = _identifier(df, columns, f"person_{group}_id")
    if own is not None:
        groups = _as_integers(own)
    elif membership is not None:
        groups = _as_integers(membership)
        if _holds_floats(membership) and (np.abs(groups) >= FLOAT32_EXACT_LIMIT).any():
            # Exact as given, but perhaps rounded before: by the model's
            # 32-bit storage of person_<group>_id, then saved as wider floats.
            warnings.warn(
                f"Column {membership.name!r} names each person's {group} with "
                f"float identifiers of {FLOAT32_EXACT_LIMIT:,} or more. If they "
                f"come from the model's 32-bit person_{group}_id, neighbouring "
                f"{group}s may share one. Add a '{group}_id' column of integers "
                "to be sure.",
                stacklevel=2,
            )
    else:
        return person_ids
    if own is not None and membership is not None:
        differs = _differs(groups, membership)
        if differs.any():
            row = int(np.flatnonzero(differs)[0])
            raise ValueError(
                f"Columns {own.name!r} and {membership.name!r} put the person "
                f"in row {row} in different groups ({groups[row]} and "
                f"{membership.iloc[row]})."
            )
    return groups


def _holds_floats(identifiers: pd.Series) -> bool:
    values = identifiers.to_numpy()
    if values.dtype.kind == "O":
        return any(_is_float(value) for value in values)
    return values.dtype.kind == "f"


def _is_whole_year(period) -> bool:
    """Whether ``period`` is one calendar year, the period of a dataset
    year."""
    start = period.start
    return (
        period.unit == "year"
        and period.size == 1
        and (start.month, start.day) == (1, 1)
    )


def _same(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Whether each pair of values is equal, counting two missing values as
    equal."""
    return np.asarray(left == right) | (pd.isna(left) & pd.isna(right))


def dataset_from_input_dataframe(
    df: pd.DataFrame,
    tax_benefit_system: "TaxBenefitSystem",
    default_year: int,
) -> Tuple[UKMultiYearDataset, List[Input], List[Input]]:
    """The dataset that an input DataFrame describes.

    The dataset holds a year for each whole-year period the frame gives
    values for, besides identifiers (or, if there is none, each whole year its
    identifier columns name, or else ``default_year``), each with the same
    people, benefit units and households, identified by 64-bit integers.
    Benefit units and households are in order of their identifiers, which is
    the order ``Simulation.build_from_ids`` gives them. Columns that do not
    name a variable of ``tax_benefit_system`` are left out.

    Args:
        df: One row per person and a column per input, named
            ``variable__period``.
        tax_benefit_system: The model whose variables the columns name.
        default_year: The year to hold the people and groups in when no
            column names a whole year.

    Returns:
        The dataset, and two lists of inputs to set after loading it.

        The first is every column of each variable the frame also gives for a
        period that is not one whole year (such as a month), which a dataset
        cannot hold, in the frame's column order. Clear those variables, then
        set these. A year's value spreads over the months that are not
        already set, so the order decides the months' values, as it did when
        each column was set in turn.

        The second is the identifiers for each whole year an identifier
        column names that is not a year of the dataset.

    Raises:
        ValueError: If a column is not named ``variable__period``, the frame
            has no ``person_id`` column or repeats a person's identifier, an
            identifier is missing, is not a whole number, does not fit in 64
            bits or is a float that may stand for more than one, identifier
            columns contradict each other,
            or the members of a benefit unit or household give different
            values for one of its variables.
    """
    if not df.columns.is_unique:
        duplicated = df.columns[df.columns.duplicated()][0]
        raise ValueError(f"Column {duplicated!r} appears more than once.")
    columns = {column: split_column(column) for column in df.columns}

    person_column = _identifier(df, columns, "person_id")
    if person_column is None:
        raise ValueError(
            "The DataFrame needs a person_id column, such as "
            f"'person_id{COLUMN_SEPARATOR}{default_year}'."
        )
    person_ids = _as_integers(person_column)
    unique_people, counts = np.unique(person_ids, return_counts=True)
    if (counts > 1).any():
        raise ValueError(
            f"Column {person_column.name!r} repeats {unique_people[counts > 1][0]}. "
            "Each row is one person with an identifier of their own."
        )
    person_groups, group_ids, first_members, group_indices = {}, {}, {}, {}
    for group in GROUP_ENTITIES:
        person_groups[group] = _group_of_each_person(df, columns, group, person_ids)
        (
            group_ids[group],
            first_members[group],
            group_indices[group],
        ) = np.unique(person_groups[group], return_index=True, return_inverse=True)

    def no_tables() -> Dict[str, Dict[str, np.ndarray]]:
        return {"person": {}, "benunit": {}, "household": {}}

    # The columns of each year's person, benefit unit and household tables.
    # Identifiers hold for every period, so the period an identifier column
    # names adds no year; the dataset's years are those its data names. The
    # first of them is the data year that some formulas read from the
    # dataset (State Pension), so a year with no data must not come first.
    years: Dict[int, Dict[str, Dict[str, np.ndarray]]] = {}
    identifier_years = set()
    # Every input of the model the frame gives, and whether it is for one
    # whole year, in column order.
    inputs: List[Tuple[Input, bool]] = []
    for column, (variable, period_text) in columns.items():
        if variable not in tax_benefit_system.variables:
            continue
        period = period_(period_text)
        start = period.start
        whole_year = _is_whole_year(period)
        if variable in IDENTIFIER_VARIABLES:
            if whole_year:
                identifier_years.add(start.year)
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
            years.setdefault(start.year, no_tables())[entity][variable] = values
        inputs.append(((variable, period_text, values), whole_year))

    in_other_periods = {
        variable for (variable, _, _), whole_year in inputs if not whole_year
    }
    replayed = [each for each, _ in inputs if each[0] in in_other_periods]

    if not years:
        # A frame of identifiers alone (and perhaps values for months).
        for year in sorted(identifier_years) or [int(default_year)]:
            years[year] = no_tables()
    person_identifiers = {
        "person_id": person_ids,
        "person_benunit_id": person_groups["benunit"],
        "person_household_id": person_groups["household"],
    }
    group_identifiers = {f"{group}_id": group_ids[group] for group in GROUP_ENTITIES}
    # The dataset holds the identifiers in each of its years, and inputs carry
    # forward but not back. So a year an identifier column names that comes
    # before the data, or between its years, needs them set as well.
    identifier_inputs = [
        (variable, str(year), values)
        for year in sorted(identifier_years - set(years))
        for variable, values in {**person_identifiers, **group_identifiers}.items()
    ]
    datasets = [
        UKSingleYearDataset(
            person=pd.DataFrame({**person_identifiers, **tables["person"]}),
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
    return UKMultiYearDataset(datasets=datasets), replayed, identifier_inputs


def with_identifiers_in_each_year(
    df: pd.DataFrame, tax_benefit_system: "TaxBenefitSystem"
) -> pd.DataFrame:
    """``df``, an exported frame, with each identifier it gives for some year
    given for every whole calendar year a column of the frame names.

    ``dataset_from_input_dataframe`` holds every identifier in each such year:
    a year a column of another variable names is a year of the dataset, which
    holds the people and groups, and each other year an identifier column
    names gets them all as inputs. So a simulation built from the frame holds
    the identifiers as inputs in those years, and exports them there.

    The simulation that exported the frame may not have. One given an input
    for a year after its data once it was built, as the Universal Credit
    rebalancing records each benefit unit's health element status for 2026
    to 2029, holds its identifiers in that year only by carrying them forward
    from an earlier one; and in a year before its data, where inputs do not
    carry back, its identifiers are the default, zero. policyengine-core
    exports an
    input only for the periods it was set for. Giving every identifier for
    each year makes the frame load back to a simulation that exports the
    same frame.

    A simulation holds one set of people and groups, so every column of an
    identifier names the same ones (the loader refuses a frame whose columns
    differ). An identifier added for a year copies its column for the latest
    year before it the frame gives, or else the earliest year it gives. Each
    goes beside the identifier's other columns, in order of period, which is
    where the default export (sorted by period) puts an input set for that
    year.

    Only columns that name a variable of ``tax_benefit_system`` count, and an
    identifier the frame does not give for any year is not added. ``df`` is
    not changed.
    """
    named: Dict[str, Dict[int, object]] = {}
    years = set()
    for column in df.columns:
        variable, period_text = split_column(column)
        if variable not in tax_benefit_system.variables:
            continue
        period = period_(period_text)
        if not _is_whole_year(period):
            continue
        if variable in IDENTIFIER_VARIABLES:
            named.setdefault(variable, {})[period.start.year] = column
        years.add(period.start.year)
    added = {
        variable: sorted(years - set(columns))
        for variable, columns in named.items()
        if years - set(columns)
    }
    if not added:
        return df
    result = df.copy(deep=False)
    for variable, missing in added.items():
        columns = named[variable]
        for year in missing:
            earlier = [named_year for named_year in columns if named_year < year]
            source = columns[max(earlier) if earlier else min(columns)]
            name = f"{variable}{COLUMN_SEPARATOR}{year}"
            # The identifier's columns, by period text, as the exporter sorts
            # them; the new one goes before the first that sorts after it.
            own = [
                position
                for position, column in enumerate(result.columns)
                if split_column(column)[0] == variable
            ]
            later = [
                position
                for position in own
                if split_column(result.columns[position])[1] > str(year)
            ]
            result.insert(later[0] if later else own[-1] + 1, name, df[source].copy())
    return result
