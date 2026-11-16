"""Which series a UK dataset's savings income was calibrated to grow by.

A dataset's savings amounts are fitted to targets that its builder moved to
the dataset year and beyond with some growth path. Dataset projection must
grow them by the same path, or the projected totals miss the targets. So the
dataset declares the path, in an H5 root attribute, and projection follows
the declaration.

- ``gdp_per_head``: GDP per head in every year. Datasets that declare nothing
  get this rule, which is how savings income was projected before the OBR
  series was added.
- ``obr_savings_income_2022_2025``: the OBR's savings income forecast per
  person from 2022-23 to 2025-26, and GDP per head in other years.

A rule's name fixes its years, so data built under one rule keeps its meaning
if a later rule covers other years.
"""

from pathlib import Path

import h5py

SAVINGS_INCOME_PROJECTION_KEY = "policyengine_uk.savings_income_projection"
GDP_PER_HEAD = "gdp_per_head"
OBR_SAVINGS_INCOME_2022_2025 = "obr_savings_income_2022_2025"
DEFAULT_SAVINGS_INCOME_PROJECTION = GDP_PER_HEAD

# The fiscal years (by starting year) in which each rule grows savings income
# by the OBR's savings income series per person, or None for no years.
SAVINGS_INCOME_SERIES_YEARS = {
    GDP_PER_HEAD: None,
    OBR_SAVINGS_INCOME_2022_2025: (2022, 2025),
}


def _error(message):
    return ValueError("Savings income projection: " + message)


def validate_savings_income_projection(rule) -> str:
    if not isinstance(rule, str) or rule not in SAVINGS_INCOME_SERIES_YEARS:
        raise _error(
            f"unknown rule {rule!r}; expected one of "
            f"{sorted(SAVINGS_INCOME_SERIES_YEARS)}."
        )
    return rule


def read_savings_income_projection(path) -> str | None:
    """The rule an H5 file declares, or None if it declares none."""
    if path is None or not Path(path).is_file() or Path(path).suffix != ".h5":
        return None
    with h5py.File(path, "r") as file:
        if SAVINGS_INCOME_PROJECTION_KEY not in file.attrs:
            return None
        rule = file.attrs[SAVINGS_INCOME_PROJECTION_KEY]
    if isinstance(rule, bytes):
        try:
            rule = rule.decode("utf-8")
        except UnicodeError as error:
            raise _error("malformed H5 metadata.") from error
    return validate_savings_income_projection(rule)


def write_savings_income_projection(path, rule) -> None:
    with h5py.File(path, "a") as file:
        file.attrs[SAVINGS_INCOME_PROJECTION_KEY] = validate_savings_income_projection(
            rule
        )


def resolve_savings_income_projection(explicit, stored) -> str:
    """An absent declaration is the default, not a contradictory one."""
    explicit = (
        None if explicit is None else validate_savings_income_projection(explicit)
    )
    stored = None if stored is None else validate_savings_income_projection(stored)
    if explicit is not None and stored is not None and explicit != stored:
        raise _error("explicit object and file metadata disagree.")
    return explicit or stored or DEFAULT_SAVINGS_INCOME_PROJECTION


def uniform_savings_income_projection(rules) -> str:
    """The one rule a multi-year dataset's years share."""
    rules = {validate_savings_income_projection(rule) for rule in rules}
    if len(rules) > 1:
        raise _error(f"a dataset's years declare different rules: {sorted(rules)}.")
    return rules.pop() if rules else DEFAULT_SAVINGS_INCOME_PROJECTION


def core_dataset_savings_income_projection(dataset) -> str:
    """Read a Core dataset's declaration without its dynamic variable lookup."""
    try:
        explicit = object.__getattribute__(dataset, "savings_income_projection")
    except AttributeError:
        explicit = None
    return resolve_savings_income_projection(
        explicit,
        read_savings_income_projection(getattr(dataset, "file_path", None)),
    )
