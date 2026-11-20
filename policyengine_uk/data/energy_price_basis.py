"""Declared price periods for stored annual energy spending."""

from collections.abc import Mapping
from dataclasses import dataclass
import inspect
import json
from pathlib import Path

import h5py


ENERGY_PRICE_BASIS_ATTRIBUTE = "energy_price_basis"


@dataclass(frozen=True)
class EnergyPriceBasis:
    """The declared annual price period of supplied energy amounts."""

    period_type: str
    period_value: int

    def __post_init__(self) -> None:
        if not isinstance(self.period_type, str) or self.period_type not in (
            "calendar_year",
            "fiscal_year",
        ):
            raise ValueError(
                "energy_price_basis period_type must be calendar_year or fiscal_year"
            )
        if type(self.period_value) is not int or not 1 <= self.period_value <= 9999:
            raise ValueError(
                "energy_price_basis period_value must be an integer year from 1 to 9999"
            )

    def as_dict(self) -> dict[str, str | int]:
        return {"period_type": self.period_type, "period_value": self.period_value}


def parse_energy_price_basis(value: object) -> EnergyPriceBasis | None:
    """Validate an explicit declaration without inferring a missing period."""
    if value is None or isinstance(value, EnergyPriceBasis):
        return value
    if not isinstance(value, Mapping) or set(value) != {"period_type", "period_value"}:
        raise ValueError(
            "energy_price_basis must contain only period_type and period_value"
        )
    return EnergyPriceBasis(value["period_type"], value["period_value"])


def merge_energy_price_basis(
    declared: object, stored: object
) -> EnergyPriceBasis | None:
    """Accept matching caller/file declarations and reject a conflict."""
    declared = parse_energy_price_basis(declared)
    stored = parse_energy_price_basis(stored)
    if declared is not None and stored is not None and declared != stored:
        raise ValueError("Conflicting energy_price_basis declarations")
    return declared if declared is not None else stored


def read_energy_price_basis(
    file_path: str | Path, group: str = "/"
) -> EnergyPriceBasis | None:
    """Read a declaration without modifying the source H5 file."""
    with h5py.File(file_path, "r") as file:
        if group not in file:
            return None
        value = file[group].attrs.get(ENERGY_PRICE_BASIS_ATTRIBUTE)
    if value is None:
        return None
    try:
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if not isinstance(value, str):
            raise ValueError("expected a JSON object")
        value = json.loads(value)
    except (UnicodeError, TypeError, ValueError) as error:
        raise ValueError("Invalid energy_price_basis JSON declaration") from error
    return parse_energy_price_basis(value)


def write_energy_price_basis(
    file_path: str | Path, value: object, group: str = "/"
) -> None:
    """Write only the energy declaration, preserving unrelated H5 attributes."""
    basis = parse_energy_price_basis(value)
    with h5py.File(file_path, "r+") as file:
        attributes = file[group].attrs
        if basis is None:
            if ENERGY_PRICE_BASIS_ATTRIBUTE in attributes:
                del attributes[ENERGY_PRICE_BASIS_ATTRIBUTE]
        else:
            attributes[ENERGY_PRICE_BASIS_ATTRIBUTE] = json.dumps(
                basis.as_dict(), sort_keys=True
            )


def core_dataset_energy_price_basis(dataset: object) -> EnergyPriceBasis | None:
    """Read explicit Core object/file provenance before schema conversion."""
    # Core's __getattr__ reads HDF keys, so inspect only declared attributes.
    declared = inspect.getattr_static(dataset, ENERGY_PRICE_BASIS_ATTRIBUTE, None)
    file_path = inspect.getattr_static(dataset, "file_path", None)
    stored = None
    if (
        isinstance(file_path, (str, Path))
        and Path(file_path).suffix == ".h5"
        and Path(file_path).is_file()
    ):
        stored = read_energy_price_basis(file_path)
    return merge_energy_price_basis(declared, stored)
