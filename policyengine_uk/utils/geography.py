"""Resolve household geography without treating Core's padding as input.

Core records whole input arrays. UK situations additionally retain which cells
of these four arrays the caller supplied. The immutable holder records follow
Core's ordinary clone/population-copy path; values remain in Core storage.
"""

import csv
from functools import lru_cache
from pathlib import Path

import numpy as np
from policyengine_core.holders.helpers import get_stored_input
from policyengine_core.periods import period as period_

from policyengine_uk.utils.supplied_inputs import _is_model_value


GEOGRAPHY_FIELDS = frozenset({"region", "country", "local_authority", "brma"})
GEOGRAPHY_MASKS = "policyengine_uk.geography_input_masks"
_HOLDER_MASKS = "_uk_geography_input_masks"
_DEVOLVED = frozenset({"SCOTLAND", "WALES", "NORTHERN_IRELAND"})


@lru_cache(maxsize=1)
def council_regions() -> dict:
    """Existing council enum keys mapped by the two documented ONS lookups."""
    path = Path(__file__).parents[1] / "data/geography/local_authority_regions.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["local_authority"]: row["region"] for row in csv.DictReader(stream)}


def country_from_region(region):
    """Country enum names for an array of Region enum names."""
    region = np.asarray(region)
    return np.where(np.isin(region, tuple(_DEVOLVED) + ("UNKNOWN",)), region, "ENGLAND")


def _names(values, possible_values):
    return possible_values.encode(values).decode_to_str()


def _visible_branches(simulation):
    return simulation._get_visible_branch_names()


def _cell_mask(holder, branch, period):
    key = (branch, str(period))
    for recorded, mask in getattr(holder, _HOLDER_MASKS, ()):
        if recorded == key:
            return np.asarray(mask, dtype=bool)
    # Array APIs and direct Core builders supply whole arrays. Only the UK
    # situation builder retains lossless sparse-cell presence.
    return np.ones(holder.population.count, dtype=bool)


def set_cell_mask(simulation, name, period, mask, *, branch=None) -> None:
    holder = simulation.get_holder(name)
    key = (simulation.branch_name if branch is None else branch, str(period_(period)))
    records = tuple(
        item for item in getattr(holder, _HOLDER_MASKS, ()) if item[0] != key
    )
    setattr(holder, _HOLDER_MASKS, records + ((key, tuple(bool(x) for x in mask)),))


def input_facts(population, name, period, *, exact=False, before=False, override=None):
    """Latest genuinely supplied cells, their presence and source periods.

    Read exact stored input tiers rather than cached/carried values. An
    optional prospective whole-array input supports validation before mutation.
    """
    simulation = population.simulation
    holder = population.get_holder(name)
    values = np.full(population.count, holder.variable.default_value.name, dtype=object)
    found = np.zeros(population.count, dtype=bool)
    sources = np.full(population.count, None, dtype=object)
    branches = _visible_branches(simulation)
    known = set(holder.get_known_branch_periods())
    if override is not None and override[0] == name:
        known.add((simulation.branch_name, period_(override[1])))
    ordered = sorted(
        ((branch, p) for branch, p in known if branch in branches),
        key=lambda item: (item[1].start, item[1].stop, -branches.index(item[0])),
        reverse=True,
    )
    for branch, source in ordered:
        if source.start > period.start or (before and source.start == period.start):
            continue
        if exact and source != period:
            continue
        prospective = (
            override is not None
            and override[0] == name
            and branch == simulation.branch_name
            and source == period_(override[1])
        )
        if prospective:
            array = np.atleast_1d(np.asarray(override[2]))
            if len(array) != population.count:
                raise ValueError(
                    f"Unable to set {name}: its input length is {len(array)} "
                    f"while the simulation has {population.count} households."
                )
            array = holder.variable.possible_values.encode(array)
            mask = np.ones(population.count, dtype=bool)
        else:
            array = get_stored_input(holder, source, branch)
            if array is None or _is_model_value(
                simulation, (name, branch, source), array
            ):
                continue
            mask = _cell_mask(holder, branch, source)
        take = mask & ~found
        if take.any():
            values[take] = _names(array, holder.variable.possible_values)[take]
            sources[take] = str(source)
            found |= take
    return values, found, sources


def _resolve(region, council, country):
    regions, has_region = region[:2]
    councils, has_council = council[:2]
    countries, has_country = country[:2]
    mapping = council_regions()
    from_council = np.array([mapping.get(value, "UNKNOWN") for value in councils])
    known_region = has_region & (regions != "UNKNOWN")
    known_country = has_country & (countries != "UNKNOWN")
    mismatch = (
        (known_region & has_council & (regions != from_council))
        | (known_region & known_country & (country_from_region(regions) != countries))
        | (
            has_council
            & known_country
            & (country_from_region(from_council) != countries)
        )
    )
    if mismatch.any():
        rows = np.flatnonzero(mismatch).tolist()
        raise ValueError(
            "Contradictory supplied region, country or local_authority "
            f"for household positions {rows}."
        )
    from_country = np.where(
        np.isin(countries, tuple(_DEVOLVED) + ("UNKNOWN",)), countries, "LONDON"
    )
    return np.where(
        has_region,
        regions,
        np.where(
            has_council, from_council, np.where(has_country, from_country, "LONDON")
        ),
    )


def resolved_region(population, period, *, override=None):
    """Region from genuine region/council/country facts, in that order."""
    return _resolve(
        *(
            input_facts(population, name, period, override=override)
            for name in ("region", "local_authority", "country")
        )
    )


def source_periods(population):
    """Actual geography input dates, including dates with partial presence."""
    simulation = population.simulation
    branches = set(_visible_branches(simulation))
    return {
        period
        for name in GEOGRAPHY_FIELDS
        for branch, period in population.get_holder(name).get_known_branch_periods()
        if branch in branches
        and get_stored_input(population.get_holder(name), period, branch) is not None
    }


def validate_geography(simulation, *, override=None) -> None:
    population = simulation.populations["household"]
    years = source_periods(population)
    if override is not None:
        years.add(period_(override[1]))
    for period in years:
        resolved_region(population, period, override=override)


def situation_presence(situation, default_period):
    """Capture sparse raw cells before SimulationBuilder pads its arrays."""
    households = situation.get("households")
    records = {}
    if households is None:
        households = {None: situation}
    for identifier, fields in households.items():
        for name in GEOGRAPHY_FIELDS & fields.keys():
            entries = fields[name]
            if not isinstance(entries, dict):
                entries = {default_period: entries}
            for period, value in entries.items():
                if value is not None:
                    records.setdefault((name, str(period_(period))), set()).add(
                        identifier
                    )
    return records


def install_situation_presence(simulation, records) -> None:
    population = simulation.populations["household"]
    identifiers = population.ids
    for (name, period), supplied in records.items():
        mask = np.array(
            [None in supplied or identifier in supplied for identifier in identifiers]
        )
        holder = population.get_holder(name)
        for branch, stored in holder.get_known_branch_periods():
            if (
                stored == period_(period)
                and get_stored_input(holder, stored, branch) is not None
            ):
                set_cell_mask(simulation, name, period, mask, branch=branch)
    validate_geography(simulation)


def merge_geography_formula(simulation, variable, period, native, had_array):
    """Apply active formulas only to cells without a genuine input.

    Core.calculate owns the surrounding frame, tracing, enum decoding and
    mapping. The public identity mapping makes that frame run even when a
    fast-cache entry exists.
    """
    if variable.is_neutralized or simulation._abolished(variable.name, period):
        return native
    population = simulation.get_variable_population(variable.name)
    resolved_region(population, period)
    values, supplied, _ = input_facts(
        population, variable.name, period, exact=variable.name == "brma"
    )
    if supplied.all():
        return variable.possible_values.encode(values)
    candidate = native
    if had_array:
        simulation._check_period_consistency(period, variable)
        simulation._check_for_cycle(variable.name, period)
        candidate = simulation._run_formula(variable, population, period)
        if candidate is None:
            candidate = population.get_holder(variable.name).default_array()
        if variable.defined_for is not None:
            enabled = (
                simulation.calculate(variable.defined_for, period, map_to="household")
                > 0
            )
            candidate = variable.possible_values.encode(candidate)
            candidate = np.where(
                enabled, candidate.decode_to_str(), variable.default_value.name
            )
        candidate = simulation._cast_formula_result(candidate, variable)
    return variable.possible_values.encode(
        np.where(supplied, values, _names(candidate, variable.possible_values))
    )


def brma_from_region(population, period, defaults, *, with_presence=False):
    """Existing regional default, or a genuine earlier override until a move."""
    region = population("region", period)
    region_names = _names(
        region, population.get_holder("region").variable.possible_values
    )
    by_name = {key.name: value.name for key, value in defaults.items()}
    result = np.array(
        [by_name.get(value, "MAIDSTONE") for value in region_names], dtype=object
    )
    previous, provided, sources = input_facts(population, "brma", period, before=True)
    carry = provided.copy()
    events = source_periods(population) | {period}
    for source in set(sources[provided]):
        source_period = period_(source)
        start = _names(
            population("region", source_period),
            population.get_holder("region").variable.possible_values,
        )
        for event in events:
            if source_period.start < event.start <= period.start:
                current = _names(
                    population("region", event),
                    population.get_holder("region").variable.possible_values,
                )
                carry &= ~((sources == source) & (current != start))
    result = np.where(carry, previous, result)
    return (result, carry) if with_presence else result


def _row_ids(frame, column):
    if column in frame:
        return tuple(frame[column].tolist())
    return tuple(frame.index.tolist())


def attach_household_presence(frame, simulation, period) -> None:
    """Retain sparse provenance in the existing in-memory dataset snapshot."""
    population = simulation.populations["household"]
    period = period_(period)
    ids = (
        tuple(frame.household_id.tolist())
        if "household_id" in frame
        else tuple(population.ids)
    )
    masks = []
    for name in GEOGRAPHY_FIELDS.intersection(frame.columns):
        _, mask, _ = input_facts(population, name, period)
        if name == "brma":
            from policyengine_uk.variables.household.BRMA import (
                REGION_DEFAULT_BRMA,
                brma,
            )

            formula = simulation.tax_benefit_system.get_variable(name).get_formula(
                period
            )
            if formula is brma.formula:
                _, mask = brma_from_region(
                    population, period, REGION_DEFAULT_BRMA, with_presence=True
                )
            elif formula is not None:
                mask = np.zeros(population.count, dtype=bool)
            _, exact, _ = input_facts(population, name, period, exact=True)
            mask |= exact
        masks.append(
            (
                name,
                tuple(
                    (identifier, bool(value)) for identifier, value in zip(ids, mask)
                ),
            )
        )
    frame.attrs[GEOGRAPHY_MASKS] = {
        "rows": tuple(zip(frame.index.tolist(), ids)),
        "masks": tuple(masks),
    }


def table_presence(frame, name):
    metadata = frame.attrs.get(GEOGRAPHY_MASKS)
    if metadata is None:
        return np.ones(len(frame), dtype=bool)
    records = dict(metadata["masks"])
    if name not in records:
        return np.ones(len(frame), dtype=bool)
    ids = _row_ids(frame, "household_id")
    association = dict(metadata["rows"])
    if "household_id" not in frame:
        try:
            ids = tuple(association[index] for index in frame.index)
        except KeyError as error:
            raise ValueError(
                "Geography presence metadata does not identify table rows."
            ) from error
    mask = dict(records[name])
    try:
        return np.array([mask[identifier] for identifier in ids], dtype=bool)
    except KeyError as error:
        raise ValueError(
            "Geography presence metadata does not identify household IDs."
        ) from error


def region_from_table(frame):
    """Resolve a projector's region without creating synthetic input columns."""
    defaults = {
        "region": "LONDON",
        "country": "ENGLAND",
        "local_authority": "MAIDSTONE",
    }
    facts = {}
    for name, default in defaults.items():
        values = (
            frame[name].to_numpy() if name in frame else np.full(len(frame), default)
        )
        mask = (
            table_presence(frame, name)
            if name in frame
            else np.zeros(len(frame), dtype=bool)
        )
        facts[name] = (values, mask)
    return _resolve(facts["region"], facts["local_authority"], facts["country"])


def install_table_presence(simulation, frame, period) -> None:
    for name in GEOGRAPHY_FIELDS.intersection(frame.columns):
        set_cell_mask(simulation, name, period, table_presence(frame, name))


def attach_input_frame_presence(frame, simulation) -> None:
    """Project geography masks to the required person IDs of an input frame."""
    people = next(
        (column for column in frame if str(column).startswith("person_id__")), None
    )
    if people is None:
        return
    population = simulation.populations["household"]
    ids = tuple(frame[people].tolist())
    masks = []
    for column in frame:
        name, separator, period = str(column).partition("__")
        if separator and name in GEOGRAPHY_FIELDS:
            _, mask, _ = input_facts(population, name, period_(period), exact=True)
            per_person = population.project(mask)
            masks.append(
                (
                    str(column),
                    tuple(
                        (identifier, bool(value))
                        for identifier, value in zip(ids, per_person)
                    ),
                )
            )
    frame.attrs[GEOGRAPHY_MASKS] = {"masks": tuple(masks)}


def restore_input_frame_presence(frame, dataset) -> None:
    """Translate the narrow exported masks through existing frame membership."""
    metadata = frame.attrs.get(GEOGRAPHY_MASKS)
    if metadata is None:
        return
    columns = dict(metadata["masks"])
    for year in dataset.years:
        single = dataset[year]
        person = single.person
        household = single.household
        masks = []
        for name in GEOGRAPHY_FIELDS.intersection(household.columns):
            key = f"{name}__{year}"
            if key not in columns:
                continue
            by_person = dict(columns[key])
            values = {}
            for identifier, hh in zip(person.person_id, person.person_household_id):
                if identifier not in by_person:
                    raise ValueError(
                        "Geography presence metadata is missing person IDs."
                    )
                value = by_person[identifier]
                if hh in values and values[hh] != value:
                    raise ValueError("Geography presence differs within a household.")
                values[hh] = value
            masks.append(
                (name, tuple((hh, bool(values[hh])) for hh in household.household_id))
            )
        household.attrs[GEOGRAPHY_MASKS] = {
            "rows": tuple(
                zip(household.index.tolist(), household.household_id.tolist())
            ),
            "masks": tuple(masks),
        }
        single.household = household
