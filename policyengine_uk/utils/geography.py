"""Resolve household geography without treating Core's padding as input.

Core records whole input arrays. UK situations additionally retain which cells
of these four arrays the caller supplied. The immutable holder records follow
Core's ordinary clone/population-copy path; values remain in Core storage.
"""

import csv
import sys
import warnings
from copy import deepcopy
from datetime import date
from functools import lru_cache
from pathlib import Path
from weakref import getweakrefcount as _weakref_count

import numpy as np
from policyengine_core.enums import Enum as CoreEnum, EnumArray
from policyengine_core.holders.helpers import get_stored_input
from policyengine_core.periods import period as period_

from policyengine_uk.utils.supplied_inputs import _is_model_value


GEOGRAPHY_FIELDS = frozenset({"region", "country", "local_authority", "brma"})
GEOGRAPHY_MASKS = "policyengine_uk.geography_input_masks"
_HOLDER_MASKS = "_uk_geography_input_masks"
_DEVOLVED = frozenset({"SCOTLAND", "WALES", "NORTHERN_IRELAND"})
_CORE_ENUM_DECODER = EnumArray.decode_to_str


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


@lru_cache(maxsize=16)
def _enum_name_lookup(possible_values):
    """Read-only names for an ordinary dense enum schema, never input values."""
    try:
        members = tuple(possible_values)
        indices = tuple(member.index for member in members)
        names = tuple(member.name for member in members)
    except (AttributeError, TypeError, ValueError):
        return None
    if (
        not members
        or any(type(index) is not int for index in indices)
        or indices != tuple(range(len(members)))
        or any(not isinstance(name, str) for name in names)
    ):
        return None
    # Core's np.select includes this default when choosing the string width.
    labels = np.asarray((*names, "unknown"))
    # The backing bytes are immutable; callers receive a separate gathered array.
    return np.frombuffer(labels[:-1].tobytes(), dtype=labels.dtype)


def _names(values, possible_values):
    encoded = possible_values.encode(values)
    decoder = encoded.decode_to_str
    if (
        type(encoded) is not EnumArray
        or getattr(decoder, "__func__", None) is not _CORE_ENUM_DECODER
        or getattr(decoder, "__self__", None) is not encoded
    ):
        return decoder()
    enum_class = getattr(encoded, "possible_values", None)
    if not isinstance(enum_class, type) or not issubclass(enum_class, CoreEnum):
        return decoder()
    indices = np.asarray(encoded)
    lookup = _enum_name_lookup(enum_class)
    if (
        lookup is None
        or indices.dtype.kind not in "iu"
        or np.any(indices < 0)
        or np.any(indices >= len(lookup))
    ):
        return decoder()
    return lookup[indices.reshape(-1)].reshape(indices.shape)


def _visible_branches(simulation):
    return simulation._get_visible_branch_names()


def _cell_mask(holder, branch, period):
    key = (branch, str(period))
    for recorded, (source_ids, mask) in getattr(holder, _HOLDER_MASKS, ()):
        if recorded == key:
            identifiers = tuple(holder.population.ids)
            if identifiers == source_ids:
                return np.asarray(mask, dtype=bool)
            by_id = dict(zip(source_ids, mask))
            try:
                return np.array(
                    [by_id[identifier] for identifier in identifiers], dtype=bool
                )
            except KeyError as error:
                raise ValueError(
                    "Geography presence metadata does not identify household IDs."
                ) from error
    # Array APIs and direct Core builders supply whole arrays. Only the UK
    # situation builder retains lossless sparse-cell presence.
    return np.ones(holder.population.count, dtype=bool)


def set_cell_mask(simulation, name, period, mask, *, branch=None) -> None:
    holder = simulation.get_holder(name)
    identifiers = tuple(holder.population.ids)
    mask = np.asarray(mask, dtype=bool)
    if len(identifiers) != holder.population.count or mask.shape != (len(identifiers),):
        raise ValueError("Geography presence must identify every household.")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Geography presence requires unique household IDs.")
    key = (simulation.branch_name if branch is None else branch, str(period_(period)))
    records = tuple(
        item for item in getattr(holder, _HOLDER_MASKS, ()) if item[0] != key
    )
    setattr(
        holder,
        _HOLDER_MASKS,
        records + ((key, (identifiers, tuple(bool(x) for x in mask))),),
    )


def _can_copy_full_input(values, decoded, take):
    """Use basic assignment only for complete native arrays with pure owners."""
    if (
        type(values) is not np.ndarray
        or type(decoded) is not np.ndarray
        or type(take) is not np.ndarray
    ):
        return False
    if (
        values.dtype != object
        or decoded.dtype.kind not in ("O", "U")
        or take.dtype != bool
    ):
        return False
    if values.ndim != 1 or decoded.shape != values.shape or take.shape != values.shape:
        return False
    if not bool(take.all()):
        return False
    # A temporary decoder array or a custom backing owner can have observable
    # destruction. The fallback preserves its original release ordering.
    if decoded.dtype.kind == "O":
        return decoded.base is None and _weakref_count(decoded) == 0
    owner = decoded
    while type(owner) is np.ndarray:
        if owner.dtype.hasobject or _weakref_count(owner):
            return False
        owner = owner.base
    return owner is None or type(owner) is bytes


def _standard_geography_schema(name, possible_values):
    """Only the declared UK input schemas have a provable physical meaning."""
    from policyengine_uk.variables.household.demographic.country import Country
    from policyengine_uk.variables.household.demographic.geography import Region
    from policyengine_uk.variables.household.demographic.locations import LocalAuthority

    expected = {
        "region": Region,
        "country": Country,
        "local_authority": LocalAuthority,
    }.get(name)
    if possible_values is expected:
        return True
    if (
        expected is None
        or type(possible_values) is not type(expected)
        or possible_values.__name__ != expected.__name__
    ):
        return False
    # Core loads variable files under per-system module names. Enums declared
    # beside their variable are distinct classes from the normal import.
    declared = sys.modules.get(expected.__module__)
    loaded = sys.modules.get(possible_values.__module__)
    if (
        declared is None
        or loaded is None
        or getattr(loaded, "__file__", None) != declared.__file__
        or getattr(loaded, expected.__name__, None) is not possible_values
    ):
        return False
    return tuple(
        (member.name, member.value, member.index) for member in possible_values
    ) == tuple((member.name, member.value, member.index) for member in expected)


def _physical_geography_names(array, possible_values, count):
    # This is validation, not the requested custom view. Never invoke an
    # encoder/decoder or infer a meaning for an unassociated/custom schema.
    if type(array) is not EnumArray or array.possible_values is not possible_values:
        return None
    names = _enum_name_lookup(possible_values)
    if names is None or array.dtype != np.dtype(np.int16) or array.shape != (count,):
        return None
    indices = np.ndarray.view(array, np.ndarray)
    if np.any(indices < 0) or np.any(indices >= len(names)):
        return None
    return names[indices]


def _physical_supplied_names(array, possible_values):
    names = _enum_name_lookup(possible_values)
    if names is None:
        return None
    allowed = frozenset(names.tolist())
    result = []
    for value in array:
        if type(value) in (str, np.str_) and value in allowed:
            result.append(str(value))
        elif type(value) is possible_values and value.name in allowed:
            if not 0 <= value.index < len(names) or names[value.index] != value.name:
                return None
            result.append(value.name)
        else:
            return None
    return np.asarray(result)


def input_facts(
    population,
    name,
    period,
    *,
    exact=False,
    before=False,
    override=None,
    with_sources: bool = True,
    _source_order=None,
    _physical=False,
    _opaque=None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Latest genuinely supplied cells, their presence and source periods.

    Read exact stored input tiers rather than cached/carried values. An
    optional prospective whole-array input supports validation before mutation.
    With ``with_sources=False``, omit source-period bookkeeping and return
    ``None`` in the third slot; values, presence and validation are unchanged.
    """
    simulation = population.simulation
    holder = population.get_holder(name)
    values = np.full(population.count, holder.variable.default_value.name, dtype=object)
    found = np.zeros(population.count, dtype=bool)
    # Physical proof and chronological coverage are different. A genuine
    # opaque fact covers its cells without assigning it a guessed meaning.
    covered = np.zeros(population.count, dtype=bool) if _physical else found
    sources = np.full(population.count, None, dtype=object) if with_sources else None
    branches = _visible_branches(simulation)
    known = set(holder.get_known_branch_periods())
    if override is not None and override[0] == name:
        known.add((simulation.branch_name, period_(override[1])))
    ordered = sorted(
        (
            (branch, p)
            for branch, p in known
            if branch in branches
            and p.start <= period.start
            and not (before and p.start == period.start)
            and (not exact or p == period)
        ),
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
            if _physical:
                decoded = (
                    _physical_supplied_names(array, holder.variable.possible_values)
                    if _standard_geography_schema(name, holder.variable.possible_values)
                    else None
                )
            else:
                array = holder.variable.possible_values.encode(array)
            mask = np.ones(population.count, dtype=bool)
        else:
            array = get_stored_input(holder, source, branch)
            if array is None or _is_model_value(
                simulation, (name, branch, source), array
            ):
                continue
            mask = _cell_mask(holder, branch, source)
        take = mask & ~covered
        if take.any():
            if _physical:
                decoded = (
                    decoded
                    if prospective
                    else _physical_geography_names(
                        array, holder.variable.possible_values, population.count
                    )
                    if _standard_geography_schema(name, holder.variable.possible_values)
                    else None
                )
                covered |= take
                if decoded is None:
                    if _opaque is not None:
                        _opaque[take] = True
                    if _source_order is not None:
                        _source_order[take, 0] = source.start.date.toordinal()
                        _source_order[take, 1] = source.stop.date.toordinal()
                    if override is None and covered.all():
                        break
                    continue
            else:
                decoded = _names(array, holder.variable.possible_values)
            if _can_copy_full_input(values, decoded, take):
                try:
                    values[:] = decoded
                finally:
                    del decoded
            else:
                try:
                    selected = decoded[take]
                finally:
                    del decoded
                try:
                    values[take] = selected
                finally:
                    del selected
            if sources is not None:
                sources[take] = str(source)
            if _source_order is not None:
                # Private, per-call primitive metadata used by chronology;
                # no string source vector or holder/array ownership escapes.
                _source_order[take, 0] = source.start.date.toordinal()
                _source_order[take, 1] = source.stop.date.toordinal()
            found |= take
        if override is None and covered.all():
            break
    return values, found, sources


def _source_ranks(*facts):
    """Compare actual source periods with the existing start/stop ordering."""
    sources = [
        fact[2]
        if len(fact) > 2 and fact[2] is not None
        else np.full(len(fact[0]), None, dtype=object)
        for fact in facts
    ]
    periods = {
        value for values in sources for value in set(values) if value is not None
    }
    keys = {value: (period_(value).start, period_(value).stop) for value in periods}
    ordered = {key: index for index, key in enumerate(sorted(set(keys.values())))}
    order = {value: ordered[key] for value, key in keys.items()}
    ranks = []
    for values in sources:
        rank = np.full(len(values), -1, dtype=np.int32)
        for value in set(values):
            if value is not None:
                rank[values == value] = order[value]
        ranks.append(rank)
    return ranks


def _decision(region, council, country, *, order=None, opaque=None):
    regions, has_region = region[:2]
    councils, has_council = council[:2]
    countries, has_country = country[:2]
    mapping = council_regions()
    if getattr(regions, "dtype", None) == object and not has_council.any():
        from_council = np.full(np.shape(councils), "UNKNOWN", dtype=object)
    else:
        # Native fixed-width arrays retain the baseline padded-name width.
        from_council = np.array([mapping.get(value, "UNKNOWN") for value in councils])
    if order is None:
        region_rank, council_rank = _source_ranks(region, council)
        council_later = council_rank > region_rank
        region_later = region_rank > council_rank
    else:
        region_order, council_order = order
        council_later = (council_order[:, 0] > region_order[:, 0]) | (
            (council_order[:, 0] == region_order[:, 0])
            & (council_order[:, 1] > region_order[:, 1])
        )
        region_later = (region_order[:, 0] > council_order[:, 0]) | (
            (region_order[:, 0] == council_order[:, 0])
            & (region_order[:, 1] > council_order[:, 1])
        )
    if opaque is None:
        later_council = has_region & has_council & council_later
    else:
        opaque_region, opaque_council = opaque[:2]
        later_council = (
            (has_region | opaque_region)
            & (has_council | opaque_council)
            & council_later
        )
    stale_council = has_region & has_council & region_later & (regions != from_council)
    effective_region = has_region & ~later_council
    effective_council = has_council & ~stale_council
    if opaque is not None:
        effective_council &= ~(opaque_region & region_later)
    known_region = effective_region & (regions != "UNKNOWN")
    known_council = effective_council & (from_council != "UNKNOWN")
    known_country = has_country & (countries != "UNKNOWN")
    region_country = country_from_region(regions)
    council_country = country_from_region(from_council)
    nations = (
        (known_region & known_council & (region_country != council_country))
        | (known_region & known_country & (region_country != countries))
        | (known_council & known_country & (council_country != countries))
    )
    mismatch = nations | (known_region & known_council & (regions != from_council))
    from_country = np.where(
        np.isin(countries, tuple(_DEVOLVED) + ("UNKNOWN",)), countries, "LONDON"
    )
    winner = np.where(
        effective_region,
        "region",
        np.where(
            effective_council,
            "local_authority",
            np.where(has_country, "country", "default"),
        ),
    )
    values = np.where(
        effective_region,
        regions,
        np.where(
            effective_council,
            from_council,
            np.where(has_country, from_country, "LONDON"),
        ),
    )
    return {
        "values": values,
        "region": effective_region,
        "local_authority": effective_council,
        "stale_council": stale_council,
        "nations": nations,
        "mismatch": mismatch,
        "winner": winner,
        "facts": (region, council, country),
        "order": order,
    }


def _diagnostic(decision, mask, period, identifiers, *, stale=False):
    indices = np.flatnonzero(mask)
    details = []
    for index in indices[:3]:
        fields = []
        for name, fact in zip(
            ("region", "local_authority", "country"), decision["facts"]
        ):
            values, present = fact[:2]
            if present[index]:
                source = (
                    fact[2][index] if len(fact) > 2 and fact[2] is not None else period
                )
                if decision.get("order") is not None and name in (
                    "region",
                    "local_authority",
                ):
                    start, stop = decision["order"][
                        ("region", "local_authority").index(name)
                    ][index]
                    first, last = (
                        date.fromordinal(int(start)),
                        date.fromordinal(int(stop)),
                    )
                    source = (
                        str(first.year)
                        if first.month == first.day == 1
                        and last.year == first.year
                        and last.month == 12
                        and last.day == 31
                        else f"{first.isoformat()}..{last.isoformat()}"
                    )
                status = (
                    " (superseded)"
                    if name == "region" and not decision["region"][index]
                    else " (stale)"
                    if name == "local_authority" and decision["stale_council"][index]
                    else ""
                )
                fields.append(f"{name}@{source}={values[index]}{status}")
        selected = (
            "stale local_authority; provide a council compatible with the newer region"
            if stale
            else "unresolved nation conflict"
            if decision["nations"][index]
            else f"selected field: {decision['winner'][index]}"
        )
        details.append(
            f"household {identifiers[index]}: {', '.join(fields)}; {selected}"
        )
    omitted = (
        f"; {len(indices) - 3} additional household IDs omitted"
        if len(indices) > 3
        else ""
    )
    prefix = (
        "Stale supplied local_authority"
        if stale
        else "Contradictory supplied geography"
    )
    return f"{prefix} for {len(indices)} households at requested period {period}: {' | '.join(details)}{omitted}."


def _resolve(region, council, country):
    """Compatibility surface for the existing array-only resolution tests."""
    decision = _decision(region, council, country)
    if decision["mismatch"].any():
        warnings.warn(
            _diagnostic(
                decision, decision["mismatch"], "unspecified", np.arange(len(region[0]))
            ),
            UserWarning,
            stacklevel=2,
        )
    return decision["values"]


def _mutation_stamp(simulation):
    # Existing Core counters detect setters/deletions, including a mutation
    # inside the current formula stack. No geography values are retained.
    return (
        simulation._input_epoch,
        simulation._inputs_set,
        id(simulation.populations["household"]),
    )


def _diagnostic_ids(population, period):
    """Use genuine public IDs when present, otherwise the builder's IDs."""
    simulation = population.simulation
    holder = population.get_holder("household_id")
    branches = _visible_branches(simulation)
    candidates = sorted(
        (
            (branch, source)
            for branch, source in holder.get_known_branch_periods()
            if branch in branches and source.start <= period.start
        ),
        key=lambda item: (item[1].start, item[1].stop, -branches.index(item[0])),
        reverse=True,
    )
    for branch, source in candidates:
        values = get_stored_input(holder, source, branch)
        if values is None or _is_model_value(
            simulation, ("household_id", branch, source), values
        ):
            continue
        if (
            np.shape(values) == (population.count,)
            and len(set(values)) == population.count
        ):
            return values
    return population.ids


def geography_decision(
    population, period, *, override=None, strict=True, warn=None, _physical=True
):
    """Fresh effective raw facts; one warning opportunity, then a fresh decision."""
    simulation = population.simulation

    def read():
        facts = []
        order = []
        opaque = []
        for name in ("region", "local_authority", "country"):
            current_opaque = (
                np.zeros(population.count, dtype=bool) if _physical else None
            )
            current_order = (
                np.full((population.count, 2), -1, dtype=np.int64)
                if name != "country"
                else None
            )
            values, present, sources = input_facts(
                population,
                name,
                period,
                exact=name == "country",
                override=override,
                with_sources=False,
                _source_order=current_order,
                _physical=_physical,
                _opaque=current_opaque,
            )
            variable = population.get_holder(name).variable
            abolished = getattr(simulation, "_abolished", None)
            if variable.is_neutralized or (
                abolished is not None and abolished(name, period)
            ):
                present = np.zeros(population.count, dtype=bool)
                if current_opaque is not None:
                    current_opaque[:] = False
            facts.append((values, present, sources))
            opaque.append(current_opaque)
            if current_order is not None:
                order.append(current_order)
        return _decision(*facts, order=order, opaque=opaque if _physical else None)

    decision = read()
    if warn is None:
        context = getattr(simulation, "_geography_read_context", None)
        warn = not (
            context is not None
            and context["stamp"] == _mutation_stamp(simulation)
            and str(period) in context["checked"]
        )
    before = _mutation_stamp(simulation)
    if warn and decision["mismatch"].any():
        warnings.warn(
            _diagnostic(
                decision,
                decision["mismatch"],
                period,
                _diagnostic_ids(population, period),
            ),
            UserWarning,
            stacklevel=2,
        )
        # Callback setters/deletions can alter any fact or requested holder.
        # Do not recursively warn or reuse the pre-warning decision.
        decision = read()
    decision["changed_during_warning"] = _mutation_stamp(simulation) != before
    if strict and decision["nations"].any():
        raise ValueError(
            _diagnostic(
                decision,
                decision["nations"],
                period,
                _diagnostic_ids(population, period),
            )
        )
    return decision


def resolved_region(population, period, *, override=None, _local_authority_mask=None):
    # Requested/custom views retain their existing codec dispatch. Strict
    # nation consistency belongs to independently provable physical facts at
    # the UK boundary, like the distinction for active custom formulas.
    uk = hasattr(population.simulation, "_geography_read_context")
    decision = geography_decision(
        population,
        period,
        override=override,
        strict=False,
        warn=False if uk else None,
        _physical=False,
    )
    if _local_authority_mask is not None:
        # Retain only primitive applicability, not decoded values or owners.
        _local_authority_mask.append(decision["local_authority"].copy())
    return decision["values"]


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
    """Strict completed-build check, or warning-only prospective field edit."""
    population = simulation.populations["household"]
    years = source_periods(population)
    if override is not None:
        years.add(period_(override[1]))
    for period in sorted(years, key=lambda value: (value.start, value.stop)):
        geography_decision(
            population, period, override=override, strict=override is None, warn=True
        )


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


def install_situation_presence(simulation, records, builder) -> None:
    population = simulation.populations["household"]
    identifiers = population.ids
    replicas = 1
    if builder.has_axes:
        identifiers = builder.entity_ids[population.entity.plural]
        for parallel_axes in builder.axes:
            replicas *= parallel_axes[0]["count"]
    for (name, period), supplied in records.items():
        prototype_mask = np.array(
            [None in supplied or identifier in supplied for identifier in identifiers]
        )
        mask = np.tile(prototype_mask, replicas)
        holder = population.get_holder(name)
        for branch, stored in holder.get_known_branch_periods():
            if (
                stored == period_(period)
                and get_stored_input(holder, stored, branch) is not None
            ):
                set_cell_mask(simulation, name, period, mask, branch=branch)
    if not getattr(simulation, "_geography_loading", False):
        validate_geography(simulation)


def merge_geography_formula(simulation, variable, period, native, had_array):
    """Apply only raw inputs still effective for this field and source date."""
    if variable.is_neutralized or simulation._abolished(variable.name, period):
        return native
    population = simulation.get_variable_population(variable.name)
    before_views = _mutation_stamp(simulation)
    # Preserve the legacy first validation/view scan and release its temporary
    # result before the requested field's second fresh codec read.
    output_council_mask = [] if variable.name == "local_authority" else None
    resolved_region(population, period, _local_authority_mask=output_council_mask)
    if variable.name == "country":
        # Country is exact-year and has no cross-field applicability mask.
        # The UK boundary has already checked physical facts. Reuse coverage
        # control only, not values; a callback mutation invalidates it.
        if getattr(simulation, "_geography_read_context", None) is not None:
            simulation._guard_geography_read((period,))
        else:
            geography_decision(population, period)
        decision = None
        changed = _mutation_stamp(simulation) != before_views
    else:
        decision = geography_decision(population, period)
        changed = (
            decision["changed_during_warning"]
            or _mutation_stamp(simulation) != before_views
        )
    if variable.name == "local_authority" and decision["stale_council"].any():
        raise ValueError(
            _diagnostic(
                decision,
                decision["stale_council"],
                period,
                _diagnostic_ids(population, period),
                stale=True,
            )
        )
    values, supplied, _ = input_facts(
        population,
        variable.name,
        period,
        exact=variable.name in ("country", "brma"),
        with_sources=False,
    )
    if variable.name in ("region", "local_authority"):
        proven = decision["facts"][("region", "local_authority").index(variable.name)][
            1
        ]
        # An unprovable custom schema keeps its declared per-field fallback;
        # do not guess a nation, recency exclusion or stale council from it.
        if (
            output_council_mask is not None
            and not changed
            and _mutation_stamp(simulation) == before_views
        ):
            # Physical proof may conservatively exclude an opaque newer
            # region. The existing decoded view still determines whether
            # an older, agreeing council applies to this requested output.
            supplied &= output_council_mask[0] | ~proven
        else:
            supplied &= decision[variable.name] | ~proven
    # Only still-applicable raw facts overlay the active formula.
    # The optional native attempt was withdrawn; baseline encoding remains.
    if supplied.all():
        return variable.possible_values.encode(values)
    candidate = native
    if had_array or changed:
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


def _snapshot_geography_history(simulation, period, identifiers):
    population = simulation.populations["household"]
    # Snapshot IDs can be numeric model inputs while situation population IDs
    # are builder names. Use the same table IDs as the existing presence attrs.
    assert len(identifiers) == population.count
    boundary = np.full(population.count, None, dtype=object)
    for name in ("region", "local_authority", "brma"):
        _, present, sources = input_facts(population, name, period)
        for source in set(sources[present]):
            selected = present & (sources == source)
            for old in set(boundary[selected]):
                if old is None or (period_(source).start, period_(source).stop) < (
                    period_(old).start,
                    period_(old).stop,
                ):
                    boundary[selected & (boundary == old)] = source
    boundary[np.equal(boundary, None)] = str(period)
    rows = []
    for name in ("region", "local_authority"):
        holder = population.get_holder(name)
        periods = sorted(
            {
                source
                for branch, source in holder.get_known_branch_periods()
                if branch in _visible_branches(simulation)
                and source.start <= period.start
            },
            key=lambda value: (value.start, value.stop),
            reverse=True,
        )
        before = np.zeros(population.count, dtype=bool)
        for source in periods:
            values, present, _ = input_facts(population, name, source, exact=True)
            selected = np.zeros(population.count, dtype=bool)
            for earliest in set(boundary):
                same = boundary == earliest
                if (source.start, source.stop) >= (
                    period_(earliest).start,
                    period_(earliest).stop,
                ):
                    selected |= same & present
                else:
                    selected |= same & present & ~before
            # Retain the nearest fact on/before each starting boundary too.
            for earliest in set(boundary):
                if (source.start, source.stop) <= (
                    period_(earliest).start,
                    period_(earliest).stop,
                ):
                    before |= present & (boundary == earliest)
            cells = tuple(
                (identifier, str(value))
                for identifier, value, keep in zip(identifiers, values, selected)
                if keep
            )
            if cells:
                rows.append((name, str(source), cells))
    return tuple(rows)


def _restore_snapshot_geography(simulation, metadata, period):
    if metadata.get("horizon") != str(period_(period)):
        return
    population = simulation.populations["household"]
    identifiers = tuple(population.ids)
    for name, source, cells in metadata.get("history", ()):
        if (
            name not in ("region", "local_authority")
            or period_(source).start > period_(metadata["horizon"]).start
        ):
            continue
        by_id = dict(cells)
        mask = np.array([identifier in by_id for identifier in identifiers], dtype=bool)
        if not mask.any():
            continue
        variable = population.get_holder(name).variable
        values = np.array(
            [
                by_id.get(identifier, variable.default_value.name)
                for identifier in identifiers
            ],
            dtype=object,
        )
        simulation.set_input(name, source, values)
        set_cell_mask(simulation, name, period_(source), mask)


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
        _, mask, _ = input_facts(population, name, period, exact=True)
        if name == "brma":
            from policyengine_uk.variables.household.BRMA import (
                REGION_DEFAULT_BRMA,
                brma,
            )

            formula = simulation.tax_benefit_system.get_variable(name).get_formula(
                period
            )
            native_module = sys.modules.get(brma.__module__)
            formula_module = sys.modules.get(getattr(formula, "__module__", None))
            native_class = getattr(formula_module, "brma", None)
            native_formula = formula is brma.formula or (
                native_module is not None
                and formula_module is not None
                and getattr(formula_module, "__file__", None) == native_module.__file__
                and type(native_class) is type(brma)
                and native_class.__module__ == formula.__module__
                and getattr(native_class, "formula", None) is formula
            )
            if native_formula:
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
        "horizon": str(period),
        "history": _snapshot_geography_history(simulation, period, ids),
    }


def copy_table_presence(source, target) -> None:
    """Keep household geography facts across a weighted frame's row alignment."""
    if GEOGRAPHY_MASKS in source.attrs:
        target.attrs[GEOGRAPHY_MASKS] = deepcopy(source.attrs[GEOGRAPHY_MASKS])


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


def region_from_table(frame, *, period=None):
    """Resolve a projection year; an omitted year keeps snapshot-horizon behavior."""
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
    metadata = frame.attrs.get(GEOGRAPHY_MASKS)
    requested = (
        period_(period)
        if period is not None
        else (
            period_(metadata["horizon"])
            if metadata is not None and "horizon" in metadata
            else None
        )
    )
    if metadata is not None and "history" in metadata:
        horizon = period_(metadata["horizon"])
        if "household_id" in frame:
            identifiers = tuple(frame.household_id.tolist())
        else:
            association = dict(metadata["rows"])
            identifiers = tuple(association[index] for index in frame.index)
        history = sorted(
            metadata["history"],
            key=lambda row: (period_(row[1]).start, period_(row[1]).stop),
            reverse=True,
        )
        for name in ("region", "local_authority"):
            values = np.full(len(frame), defaults[name], dtype=object)
            found = np.zeros(len(frame), dtype=bool)
            sources = np.full(len(frame), None, dtype=object)
            for field, source, cells in history:
                if field != name or period_(source).start > min(
                    horizon.start, requested.start
                ):
                    continue
                by_id = dict(cells)
                supplied = np.array(
                    [identifier in by_id for identifier in identifiers], dtype=bool
                )
                take = supplied & ~found
                current = np.array(
                    [
                        by_id.get(identifier, defaults[name])
                        for identifier in identifiers
                    ],
                    dtype=object,
                )
                values[take], sources[take] = current[take], source
                found |= take
            facts[name] = (values, found, sources)
        country, present = facts["country"]
        # A projected physical country is not a new observation. An omitted
        # period deliberately resolves at the original snapshot's horizon.
        if requested != horizon:
            present = np.zeros(len(frame), dtype=bool)
        facts["country"] = (
            country,
            present,
            np.full(len(frame), str(horizon), dtype=object),
        )
    decision = _decision(facts["region"], facts["local_authority"], facts["country"])
    if decision["mismatch"].any():
        identifiers = _row_ids(frame, "household_id")
        if metadata is not None and "household_id" not in frame:
            association = dict(metadata["rows"])
            identifiers = tuple(association[index] for index in frame.index)
        warnings.warn(
            _diagnostic(
                decision, decision["mismatch"], requested or "unspecified", identifiers
            ),
            UserWarning,
            stacklevel=2,
        )
    return decision["values"]


def install_table_presence(simulation, frame, period) -> None:
    metadata = frame.attrs.get(GEOGRAPHY_MASKS)
    for name in GEOGRAPHY_FIELDS.intersection(frame.columns):
        mask = table_presence(frame, name)
        if (
            metadata is not None
            and "horizon" in metadata
            and str(period_(period)) != metadata["horizon"]
        ):
            # Projected physical columns are not new source observations.
            mask = np.zeros(len(frame), dtype=bool)
        set_cell_mask(simulation, name, period, mask)
    if metadata is not None:
        _restore_snapshot_geography(simulation, metadata, period)


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


def _install_input_frame_presence(simulation, frame, dataset) -> None:
    """Retain the same existing masks after nonannual frame entries replay."""
    metadata = frame.attrs.get(GEOGRAPHY_MASKS)
    if metadata is None:
        return
    person = dataset[dataset.years[0]].person
    membership = dict(zip(person.person_id, person.person_household_id))
    population = simulation.populations["household"]
    for column, cells in metadata["masks"]:
        name, separator, source = str(column).partition("__")
        if not separator or name not in GEOGRAPHY_FIELDS:
            continue
        source = period_(source)
        if (
            get_stored_input(
                population.get_holder(name), source, simulation.branch_name
            )
            is None
        ):
            continue
        by_household = {}
        for identifier, present in cells:
            if identifier not in membership:
                continue
            household = membership[identifier]
            if household in by_household and by_household[household] != present:
                raise ValueError("Geography presence differs within a household.")
            by_household[household] = present
        try:
            mask = [by_household[identifier] for identifier in population.ids]
        except KeyError as error:
            raise ValueError(
                "Geography presence metadata is missing household IDs."
            ) from error
        set_cell_mask(simulation, name, source, mask)
