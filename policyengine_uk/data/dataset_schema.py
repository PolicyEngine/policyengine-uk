import warnings
import pandas as pd
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from policyengine_uk import Microsimulation

from pathlib import Path
import h5py
import json

from policyengine_uk.data.energy_price_basis import (
    EnergyPriceBasis,
    merge_energy_price_basis,
    parse_energy_price_basis,
    read_energy_price_basis,
    write_energy_price_basis,
)
from policyengine_uk.data.savings_income_projection import (
    SAVINGS_INCOME_PROJECTION_KEY,
    read_savings_income_projection,
    resolve_savings_income_projection,
    uniform_savings_income_projection,
    validate_savings_income_projection,
)
from policyengine_uk.data.isa_income import (
    ISA_INCOME_CONTRACT_KEY,
    MISSING_CONTRACT,
    contract_envelope,
    contracts_for_years,
    read_h5_contract,
    resolve_contracts,
    simulation_contract,
    validate_contract,
)


def _validate_integer_enum_positions(array, possible_values, column: str) -> None:
    """Validate zero-based positions before narrowing or indexing enum arrays.

    Integer positions are not survey source codes. Valid positions, including
    a declared UNKNOWN member, retain their existing meaning.
    """
    if array.dtype.kind not in ("i", "u"):
        return
    invalid = (array < 0) | (array >= len(possible_values))
    if np.any(invalid):
        invalid_values = np.unique(array[invalid])
        shown = invalid_values[:10].tolist()
        remainder = len(invalid_values) - len(shown)
        suffix = f" (and {remainder} other invalid positions)" if remainder else ""
        raise ValueError(
            f"Invalid integer position(s) {shown}{suffix} in column '{column}' "
            f"for enum {possible_values.__name__}. Expected zero-based positions "
            f"in [0, {len(possible_values)})."
        )


class UKSingleYearDataset:
    @staticmethod
    def validate_file_path(file_path: str, raise_exception: bool = True):
        if not file_path.endswith(".h5"):
            if raise_exception:
                raise ValueError("File path must end with '.h5' for UKDataset.")
            return False
        if not Path(file_path).exists():
            if raise_exception:
                raise FileNotFoundError(f"File not found: {file_path}")
            return False

        # Pandas stores each table as an annotated HDF5 group. A multi-year
        # file has unannotated parent groups here, with tables below the years.
        with h5py.File(file_path, "r") as f:
            required_datasets = [
                "time_period",
                "person",
                "benunit",
                "household",
            ]
            for dataset in required_datasets:
                if (
                    dataset not in f
                    or not isinstance(f[dataset], h5py.Group)
                    or "pandas_type" not in f[dataset].attrs
                ):
                    if raise_exception:
                        raise ValueError(
                            f"Dataset '{dataset}' not found in the file: {file_path}"
                        )
                    else:
                        return False

        return True

    # Used when a dataset is built from DataFrames without a fiscal year.
    # Deprecated: pass fiscal_year explicitly, as this will become required.
    DEFAULT_FISCAL_YEAR = 2025

    def __init__(
        self,
        file_path: str = None,
        person: pd.DataFrame = None,
        benunit: pd.DataFrame = None,
        household: pd.DataFrame = None,
        fiscal_year: int = None,
        energy_price_basis: dict[str, str | int] | EnergyPriceBasis | None = None,
        isa_income_contract: dict | None = None,
        savings_income_projection: str | None = None,
    ):
        basis = parse_energy_price_basis(energy_price_basis)
        file_path = str(file_path) if file_path else None
        if file_path is not None:
            if fiscal_year is not None:
                warnings.warn(
                    "fiscal_year is ignored when loading from a file: the "
                    "time period is read from the file itself. Drop the "
                    "argument, or use uprate_dataset to change the period.",
                    UserWarning,
                    stacklevel=2,
                )
            self.validate_file_path(file_path)
            # Read-only: the file may be a cached download the cache manager
            # has made unwritable, and the default append mode would refuse it.
            with pd.HDFStore(file_path, mode="r") as f:
                self._person = f["person"]
                self._benunit = f["benunit"]
                self._household = f["household"]
                self.time_period = str(f["time_period"].iloc[0])
            basis = merge_energy_price_basis(basis, read_energy_price_basis(file_path))
        else:
            if person is None or benunit is None or household is None:
                raise ValueError(
                    "Must provide either a file path or all three DataFrames (person, benunit, household)."
                )
            if fiscal_year is None:
                warnings.warn(
                    "fiscal_year was not given, so this dataset is labelled "
                    f"{self.DEFAULT_FISCAL_YEAR}. The label is the year the "
                    "financial year starts, so FRS 2024/25 data is 2024. "
                    "Pass fiscal_year explicitly; the default will be "
                    "removed.",
                    FutureWarning,
                    stacklevel=2,
                )
                fiscal_year = self.DEFAULT_FISCAL_YEAR
            self._person = person
            self._benunit = benunit
            self._household = household
            self.time_period = str(fiscal_year)

        self._energy_price_basis = basis
        self.isa_income_contract = resolve_contracts(
            MISSING_CONTRACT if isa_income_contract is None else isa_income_contract,
            read_h5_contract(file_path),
            [int(self.time_period[:4])],
        )[int(self.time_period[:4])]
        self.savings_income_projection = resolve_savings_income_projection(
            savings_income_projection, read_savings_income_projection(file_path)
        )
        self.data_format = "arrays"
        # tables tuple points at the raw (int16) DataFrames used by the
        # simulation engine internals - do not decode these.
        self.tables = (self._person, self._benunit, self._household)
        self.table_names = ("person", "benunit", "household")
        # Populated by _pre_encode_enum_columns in simulation.py after the
        # dataset is loaded and enum columns have been converted to int16.
        self._enum_columns: dict = {}

    @property
    def energy_price_basis(self) -> dict[str, str | int] | None:
        """A defensive copy of the stored amounts' declared price period."""
        return self._energy_price_basis.as_dict() if self._energy_price_basis else None

    @energy_price_basis.setter
    def energy_price_basis(self, value: object) -> None:
        self._energy_price_basis = parse_energy_price_basis(value)

    def _decode_enum_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of *df* with int16 enum columns decoded to strings."""
        if not self._enum_columns:
            return df
        enum_cols_in_df = [c for c in df.columns if c in self._enum_columns]
        if not enum_cols_in_df:
            return df
        out = df.copy()
        for col in enum_cols_in_df:
            possible_values = self._enum_columns[col]
            arr = out[col].values
            if arr.dtype.kind not in ("i", "u"):
                continue
            _validate_integer_enum_positions(arr, possible_values, col)
            names = np.array([m.name for m in possible_values], dtype=object)
            out[col] = names[arr.astype(int)]
        return out

    @property
    def person(self) -> pd.DataFrame:
        return self._decode_enum_df(self._person)

    @person.setter
    def person(self, df: pd.DataFrame):
        self._person = df
        self.tables = (self._person, self._benunit, self._household)

    @property
    def benunit(self) -> pd.DataFrame:
        return self._decode_enum_df(self._benunit)

    @benunit.setter
    def benunit(self, df: pd.DataFrame):
        self._benunit = df
        self.tables = (self._person, self._benunit, self._household)

    @property
    def household(self) -> pd.DataFrame:
        return self._decode_enum_df(self._household)

    @household.setter
    def household(self, df: pd.DataFrame):
        self._household = df
        self.tables = (self._person, self._benunit, self._household)

    def save(self, file_path: str):
        contract = validate_contract(self.isa_income_contract)
        with pd.HDFStore(file_path) as f:
            f.put("person", self.person, format="table", data_columns=True)
            f.put("benunit", self.benunit, format="table", data_columns=True)
            f.put("household", self.household, format="table", data_columns=True)
            f.put("time_period", pd.Series([self.time_period]), format="table")
        write_energy_price_basis(file_path, self._energy_price_basis)
        with h5py.File(file_path, "a") as f:
            f.attrs[ISA_INCOME_CONTRACT_KEY] = json.dumps(contract)
            f.attrs[SAVINGS_INCOME_PROJECTION_KEY] = validate_savings_income_projection(
                self.savings_income_projection
            )

    def load(self):
        data = {}
        for df in (self.person, self.benunit, self.household):
            for col in df.columns:
                data[col] = df[col].values

        return data

    def copy(self):
        return UKSingleYearDataset(
            person=self.person.copy(),
            benunit=self.benunit.copy(),
            household=self.household.copy(),
            fiscal_year=self.time_period,
            energy_price_basis=self._energy_price_basis,
            isa_income_contract=validate_contract(self.isa_income_contract),
            savings_income_projection=self.savings_income_projection,
        )

    def validate(self):
        # Check for NaNs in the tables
        for df in self.tables:
            for col in df.columns:
                if df[col].isna().any():
                    raise ValueError(f"Column '{col}' contains NaN values.")

    @staticmethod
    def from_simulation(
        simulation: "Microsimulation",
        fiscal_year: int = 2025,
        energy_price_basis: dict[str, str | int] | EnergyPriceBasis | None = None,
        savings_income_projection: str | None = None,
    ):
        entity_dfs = {}

        for entity in ["person", "benunit", "household"]:
            input_variables = [
                variable
                for variable in simulation.input_variables
                if simulation.tax_benefit_system.variables[variable].entity.key
                == entity
            ]
            if len(input_variables) == 0:
                entity_dfs[entity] = pd.DataFrame()
            else:
                entity_dfs[entity] = simulation.calculate_dataframe(
                    input_variables, period=fiscal_year
                )

        return UKSingleYearDataset(
            person=entity_dfs["person"],
            benunit=entity_dfs["benunit"],
            household=entity_dfs["household"],
            fiscal_year=fiscal_year,
            energy_price_basis=energy_price_basis,
            isa_income_contract=simulation_contract(simulation, fiscal_year),
            savings_income_projection=(
                getattr(simulation, "_savings_income_projection", None)
                if savings_income_projection is None
                else savings_income_projection
            ),
        )


class UKMultiYearDataset:
    def __init__(
        self,
        file_path: str = None,
        datasets: list[UKSingleYearDataset] | None = None,
    ):
        file_path = str(file_path) if file_path else None
        if datasets is not None:
            self.datasets = {}
            for dataset in datasets:
                if not isinstance(dataset, UKSingleYearDataset):
                    raise TypeError(
                        "All items in datasets must be of type UKSingleYearDataset."
                    )
                year = int(dataset.time_period[:4])
                self.datasets[year] = dataset
            # Projection grows every year by one declared rule.
            uniform_savings_income_projection(
                dataset.savings_income_projection for dataset in datasets
            )

        if file_path is not None:
            UKMultiYearDataset.validate_file_path(file_path)
            stored_contract = read_h5_contract(file_path)
            stored_savings_rule = read_savings_income_projection(file_path)
            with pd.HDFStore(file_path, mode="r") as f:
                self.datasets = {}
                years = [
                    int(key.split("/")[2])
                    for key in f.keys()
                    if key.startswith("/person/")
                ]
                contracts = contracts_for_years(stored_contract, years)
                for year in f.keys():
                    if year.startswith("/person/"):
                        fiscal_year = int(year.split("/")[2])
                        person_df = f[year]
                        benunit_df = f[f"/benunit/{fiscal_year}"]
                        household_df = f[f"/household/{fiscal_year}"]
                        self.datasets[fiscal_year] = UKSingleYearDataset(
                            person=person_df,
                            benunit=benunit_df,
                            household=household_df,
                            fiscal_year=fiscal_year,
                            isa_income_contract=contracts[fiscal_year],
                            savings_income_projection=stored_savings_rule,
                        )
            for year, dataset in self.datasets.items():
                dataset.energy_price_basis = read_energy_price_basis(
                    file_path, f"/time_period/{year}"
                )

        self.data_format = "time_period_arrays"
        self.time_period = list(sorted(self.datasets.keys()))[0]

    def get_year(self, fiscal_year: int) -> UKSingleYearDataset:
        if fiscal_year in self.datasets:
            return self.datasets[fiscal_year]
        else:
            raise ValueError(f"No dataset found for year {fiscal_year}.")

    @property
    def years(self):
        return list(self.datasets.keys())

    @property
    def isa_income_contract(self):
        return contract_envelope(
            {
                year: dataset.isa_income_contract
                for year, dataset in self.datasets.items()
            }
        )

    @property
    def savings_income_projection(self) -> str:
        return uniform_savings_income_projection(
            dataset.savings_income_projection for dataset in self.datasets.values()
        )

    def __getitem__(self, fiscal_year: int):
        return self.get_year(fiscal_year)

    def save(self, file_path: str):
        contracts = self.isa_income_contract
        savings_rule = self.savings_income_projection
        Path(file_path).unlink(missing_ok=True)  # Remove existing file if it exists
        with pd.HDFStore(file_path) as f:
            for year, dataset in self.datasets.items():
                f.put(
                    f"person/{year}",
                    dataset.person,
                    format="table",
                    data_columns=True,
                )

                f.put(
                    f"benunit/{year}",
                    dataset.benunit,
                    format="table",
                    data_columns=True,
                )
                f.put(
                    f"household/{year}",
                    dataset.household,
                    format="table",
                    data_columns=True,
                )
                f.put(
                    f"time_period/{year}",
                    pd.Series([year]),
                    format="table",
                    data_columns=True,
                )
        for year, dataset in self.datasets.items():
            write_energy_price_basis(
                file_path, dataset.energy_price_basis, f"/time_period/{year}"
            )

        with h5py.File(file_path, "a") as f:
            f.attrs[ISA_INCOME_CONTRACT_KEY] = json.dumps(contracts)
            f.attrs[SAVINGS_INCOME_PROJECTION_KEY] = savings_rule

    def copy(self):
        new_datasets = {year: dataset.copy() for year, dataset in self.datasets.items()}
        return UKMultiYearDataset(datasets=list(new_datasets.values()))

    @staticmethod
    def validate_file_path(file_path: str, raise_exception: bool = False):
        if not file_path.endswith(".h5"):
            if raise_exception:
                raise ValueError(
                    "File path must end with '.h5' for UKMultiYearDataset."
                )
            else:
                return False
        if not Path(file_path).exists():
            if raise_exception:
                raise FileNotFoundError(f"File not found: {file_path}")
            else:
                return False

        # h5py lists only immediate children: the entity groups contain the
        # year-named pandas tables written by save, even for a single year.
        with h5py.File(file_path, "r") as f:
            for required_dataset in ["person", "benunit", "household"]:
                if required_dataset not in f:
                    if raise_exception:
                        raise ValueError(
                            f"Dataset '{required_dataset}' not found in the file: {file_path}"
                        )
                    else:
                        return False

                group = f[required_dataset]
                years_found = (
                    isinstance(group, h5py.Group)
                    and "pandas_type" not in group.attrs
                    and any(
                        len(year) == 4
                        and year.isdigit()
                        and isinstance(group[year], h5py.Group)
                        and "pandas_type" in group[year].attrs
                        for year in group
                    )
                )

                if not years_found:
                    if raise_exception:
                        raise ValueError(
                            f"No yearly data found for '{required_dataset}' in file: {file_path}"
                        )
                    else:
                        return False
        return True

    def load(self):
        data = {}
        for year, dataset in self.datasets.items():
            for df in (dataset.person, dataset.benunit, dataset.household):
                for col in df.columns:
                    if col not in data:
                        data[col] = {}
                    data[col][year] = df[col].values
        return data

    def reset_uprating(self):
        from policyengine_uk.data.economic_assumptions import reset_uprating

        reset_uprating(self)
