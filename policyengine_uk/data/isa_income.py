"""Versioned savings-interest input semantics at UK dataset boundaries.

Legacy data holds ISA interest inside gross savings interest. Calculator
inputs and normalized datasets hold ordinary interest plus a separate tax-free
aggregate. Projection origin is independent of that representation.
"""

import copy
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from policyengine_core.periods import period as period_
from policyengine_core.simulations.simulation import (
    _latest_input_key,
    _uprating_index_value,
)


ISA_INCOME_CONTRACT_KEY = "policyengine_uk.isa_income_contract"
SAVINGS_INTEREST = "savings_interest_income"
ISA_INTEREST = "individual_savings_account_interest_income"
TAX_FREE_INTEREST = "tax_free_savings_income"
LEGACY_CONTRACT = {
    "version": 1,
    "representation": "legacy_gross",
    "projection": "legacy_gross",
}
ADDITIVE_CONTRACT = {
    "version": 1,
    "representation": "additive",
    "projection": "additive",
}
MISSING_CONTRACT = object()


def latest_input(simulation, name, period, *, earlier=False):
    """Core's branch-readable input selection, excluding calculated caches."""
    period = period_(period)
    holder = simulation.get_holder(name)
    definition_period = simulation.tax_benefit_system.variables[name].definition_period
    candidates = [
        source
        for source in holder.get_input_periods(simulation.branch_name)
        if (source.start < period.start if earlier else source.start <= period.start)
        and holder.get_array(source, simulation.branch_name) is not None
    ]
    return max(
        candidates,
        key=lambda source: _latest_input_key(source, definition_period),
        default=None,
    )


def has_isa_interest_detail_input(simulation, period):
    """Work on generic Core simulations as well as UK dataset simulations."""
    return latest_input(simulation, "non_cash_isa_cash_interest", period) is not None


def isa_interest_income_default(simulation, period):
    """Formula-only ISA detail/input fallback, valid on generic Core too.

    Core gives a supplied total for this period priority before calling the
    formula. A newer detail can supply a new observation, but a same-period
    or older of-which amount cannot replace a supplied total. Earlier totals
    carry under the legacy contract or grow by the actual ONS index under
    the additive contract. Calculated caches are never sources.
    """
    period = period_(period)
    source = latest_input(simulation, ISA_INTEREST, period)
    detail = latest_input(simulation, "non_cash_isa_cash_interest", period)
    definition_period = simulation.tax_benefit_system.variables[
        ISA_INTEREST
    ].definition_period
    if detail is not None and (
        source is None
        or _latest_input_key(detail, definition_period)
        > _latest_input_key(source, definition_period)
    ):
        return simulation.calculate("non_cash_isa_cash_interest", period)
    if source is None:
        return None
    values = simulation.get_holder(ISA_INTEREST).get_array(
        source, simulation.branch_name
    )
    if (
        simulation_contract(simulation, period.start.year)["projection"]
        == "legacy_gross"
    ):
        return values
    index = simulation.tax_benefit_system.parameters.get_child(
        "gov.economic_assumptions.indices.ons.household_interest_income"
    )
    source_index = _uprating_index_value(index, source.start)
    target_index = _uprating_index_value(index, period.start)
    factor = (
        target_index / source_index
        if source_index not in (None, 0) and target_index is not None
        else 1
    )
    return values * factor


def _error(message):
    return ValueError("ISA income contract: " + message)


def validate_contract(contract):
    if not isinstance(contract, dict) or set(contract) != {
        "version",
        "representation",
        "projection",
    }:
        raise _error("expected version, representation and projection.")
    if type(contract["version"]) is not int or contract["version"] != 1:
        raise _error("unsupported version.")
    if not all(
        isinstance(contract[key], str) for key in ("representation", "projection")
    ):
        raise _error("representation and projection must be strings.")
    pair = (contract["representation"], contract["projection"])
    if pair not in {
        ("legacy_gross", "legacy_gross"),
        ("additive", "legacy_gross"),
        ("additive", "additive"),
    }:
        raise _error("unknown or contradictory representation/projection.")
    return copy.deepcopy(contract)


def contracts_for_years(marker, years):
    """Validate a uniform contract or an envelope covering the required years."""
    years = [str(int(year)) for year in years]
    if marker is MISSING_CONTRACT:
        marker = LEGACY_CONTRACT
    if isinstance(marker, dict) and set(marker) == {"version", "years"}:
        if type(marker["version"]) is not int or marker["version"] != 1:
            raise _error("unsupported envelope version.")
        entries = marker["years"]
        if not isinstance(entries, dict):
            raise _error("years must be a mapping.")
        validated = {}
        for year, contract in entries.items():
            if (
                not isinstance(year, str)
                or not year.isdigit()
                or str(int(year)) != year
            ):
                raise _error("year keys must be fiscal-year strings.")
            validated[year] = validate_contract(contract)
        if set(years) - set(validated):
            raise _error("the envelope omits a dataset year.")
        return {int(year): copy.deepcopy(validated[year]) for year in years}
    contract = validate_contract(marker)
    return {int(year): copy.deepcopy(contract) for year in years}


def contract_envelope(contracts):
    return {
        "version": 1,
        "years": {
            str(int(year)): validate_contract(contract)
            for year, contract in sorted(contracts.items())
        },
    }


def read_h5_contract(path):
    """Read metadata without exposing it as a Core dataset variable."""
    if path is None or not Path(path).is_file() or Path(path).suffix != ".h5":
        return MISSING_CONTRACT
    with h5py.File(path, "r") as file:
        if ISA_INCOME_CONTRACT_KEY not in file.attrs:
            return MISSING_CONTRACT
        encoded = file.attrs[ISA_INCOME_CONTRACT_KEY]
    try:
        if isinstance(encoded, bytes):
            encoded = encoded.decode("utf-8")
        return json.loads(encoded)
    except (TypeError, ValueError, UnicodeError) as error:
        raise _error("malformed H5 metadata.") from error


def read_object_contract(dataset):
    """Read declared metadata without Core's dynamic dataset-variable lookup."""
    try:
        return object.__getattribute__(dataset, "isa_income_contract")
    except AttributeError:
        return MISSING_CONTRACT


def resolve_contracts(explicit, stored, years):
    """An absent declaration is a default, not a contradictory explicit one."""
    explicit_map = (
        None if explicit is MISSING_CONTRACT else contracts_for_years(explicit, years)
    )
    stored_map = (
        None if stored is MISSING_CONTRACT else contracts_for_years(stored, years)
    )
    if (
        explicit_map is not None
        and stored_map is not None
        and explicit_map != stored_map
    ):
        raise _error("explicit object and file metadata disagree.")
    return explicit_map or stored_map or contracts_for_years(MISSING_CONTRACT, years)


def interest_values(table, name):
    if name not in table:
        return np.zeros(len(table), dtype=float)
    try:
        values = pd.to_numeric(table[name], errors="raise").to_numpy(dtype=float)
    except (TypeError, ValueError) as error:
        raise _error(f"{name} must be numeric.") from error
    if not np.isfinite(values).all():
        raise _error(f"{name} must be finite.")
    return values


def effective_tax_free(table, previous_isa=None):
    # Validate both supplied inputs, even when the aggregate overrides I.
    isa = interest_values(table, ISA_INTEREST)
    if TAX_FREE_INTEREST in table:
        return interest_values(table, TAX_FREE_INTEREST)
    return isa if ISA_INTEREST in table or previous_isa is None else previous_isa


def ordinary_interest(dataset):
    contract = validate_contract(dataset.isa_income_contract)
    gross_or_ordinary = interest_values(dataset.person, SAVINGS_INTEREST)
    exempt = effective_tax_free(dataset.person)
    if (
        SAVINGS_INTEREST not in dataset.person
        and contract["projection"] == "legacy_gross"
    ):
        return -exempt
    return (
        gross_or_ordinary - exempt
        if contract["representation"] == "legacy_gross"
        else gross_or_ordinary
    )


def gross_interest(dataset):
    contract = validate_contract(dataset.isa_income_contract)
    values = interest_values(dataset.person, SAVINGS_INTEREST)
    exempt = effective_tax_free(dataset.person)
    if (
        SAVINGS_INTEREST not in dataset.person
        and contract["projection"] == "legacy_gross"
    ):
        return np.zeros(len(dataset.person), dtype=float)
    return values if contract["representation"] == "legacy_gross" else values + exempt


def normalized_single_year(dataset, previous_isa=None):
    """Detach before conversion; signed ordinary amounts preserve overrides."""
    out = dataset.copy()
    table = out.person
    exempt = effective_tax_free(table, previous_isa)
    if SAVINGS_INTEREST in table:
        values = interest_values(table, SAVINGS_INTEREST)
        if out.isa_income_contract["representation"] == "legacy_gross":
            values = values - exempt
        out.person = table.assign(**{SAVINGS_INTEREST: values})
    out.isa_income_contract = {
        **validate_contract(out.isa_income_contract),
        "representation": "additive",
    }
    return out


def normalized_dataset(dataset):
    from policyengine_uk.data.dataset_schema import UKMultiYearDataset

    # A cache stores the canonical object once. Revalidate declarations and
    # participating amounts, but retain that object on subsequent loads.
    if all(
        validate_contract(dataset[year].isa_income_contract)["representation"]
        == "additive"
        for year in dataset.years
    ):
        for year in dataset.years:
            effective_tax_free(dataset[year].person)
            interest_values(dataset[year].person, SAVINGS_INTEREST)
        return dataset

    singles = []
    previous_isa = None
    for year in sorted(dataset.years):
        single = dataset[year]
        singles.append(normalized_single_year(single, previous_isa))
        if ISA_INTEREST in single.person:
            previous_isa = interest_values(single.person, ISA_INTEREST)
    out = UKMultiYearDataset(datasets=singles)
    if hasattr(dataset, "_cgt_extension_provenance"):
        out._cgt_extension_provenance = copy.deepcopy(dataset._cgt_extension_provenance)
    return out


def legacy_projection_source(dataset):
    """Undo only representation conversion before the old gross projection."""
    contract = validate_contract(dataset.isa_income_contract)
    if contract != {**LEGACY_CONTRACT, "representation": "additive"}:
        return dataset
    out = dataset.copy()
    if SAVINGS_INTEREST in out.person:
        out.person = out.person.assign(**{SAVINGS_INTEREST: gross_interest(out)})
    out.isa_income_contract = copy.deepcopy(LEGACY_CONTRACT)
    return out


def simulation_contract(simulation, year):
    contracts = getattr(simulation, "_isa_income_contracts", {})
    year = int(str(year)[:4])
    if year in contracts:
        return validate_contract(contracts[year])
    earlier = [stored for stored in contracts if stored <= year]
    return validate_contract(contracts[max(earlier)] if earlier else ADDITIVE_CONTRACT)
