"""Whole-array and sparse-presence compatibility for geography fact reads."""

from types import SimpleNamespace

import numpy as np
import pytest
from policyengine_core.periods import period
from policyengine_core.simulations.simulation_builder import SimulationBuilder

from policyengine_uk import Simulation
from policyengine_uk.utils import geography
from policyengine_uk.utils.geography import _HOLDER_MASKS, _cell_mask, _resolve
from policyengine_uk.utils.household_subset import household_subset


@pytest.mark.parametrize("record", ["absent", "other_branch", "other_period"])
def test_absent_or_unmatched_mask_record_uses_whole_array_presence(record):
    """Only a record for this exact storage branch and period limits cells."""
    population = SimpleNamespace(ids=np.array(["c", "a", "b"]), count=3)
    holder = SimpleNamespace(population=population)
    if record != "absent":
        key = ("other", "2025") if record == "other_branch" else ("default", "2024")
        setattr(holder, _HOLDER_MASKS, ((key, (("c", "a", "b"), (False,) * 3)),))
    result = _cell_mask(holder, "default", period(2025))
    np.testing.assert_array_equal(result, [True, True, True])
    assert result.dtype == np.dtype(bool)


@pytest.mark.parametrize(
    "identifiers, expected",
    [(["a", "b", "c"], [True, False, True]), (["c", "b"], [True, False])],
)
def test_matching_presence_record_keeps_identity_alignment(identifiers, expected):
    """A real matching record follows household identity through a subset."""
    holder = SimpleNamespace(
        population=SimpleNamespace(ids=np.array(identifiers), count=len(identifiers))
    )
    source_mask = (True, False, True)
    setattr(
        holder,
        _HOLDER_MASKS,
        ((("default", "2025"), (("a", "b", "c"), source_mask)),),
    )
    result = _cell_mask(holder, "default", period(2025))
    np.testing.assert_array_equal(result, expected)
    result[0] = False
    assert source_mask == (True, False, True)


@pytest.mark.parametrize("empty", [False, True])
def test_resolve_without_council_facts_preserves_outputs(empty):
    """Padding is not a council fact; explicit UNKNOWN and defaults survive."""
    regions = np.array(
        []
        if empty
        else ["UNKNOWN", "UNKNOWN", "LONDON", "UNKNOWN", "UNKNOWN", "UNKNOWN"],
        dtype=object,
    )
    countries = np.array(
        []
        if empty
        else [
            "SCOTLAND",
            "WALES",
            "ENGLAND",
            "NORTHERN_IRELAND",
            "UNKNOWN",
            "SCOTLAND",
        ],
        dtype=object,
    )
    has_region = np.array(
        [] if empty else [False, False, True, False, False, True], dtype=bool
    )
    has_country = np.array(
        [] if empty else [True, True, True, True, True, False], dtype=bool
    )
    councils = np.full(len(regions), "MAIDSTONE", dtype=object)
    no_council = np.zeros(len(regions), dtype=bool)
    result = _resolve(
        (regions, has_region), (councils, no_council), (countries, has_country)
    )
    expected = (
        []
        if empty
        else ["SCOTLAND", "WALES", "LONDON", "NORTHERN_IRELAND", "UNKNOWN", "UNKNOWN"]
    )
    np.testing.assert_array_equal(result, np.array(expected, dtype=object))
    assert result.dtype == np.dtype(object)
    if not empty:
        # With native fixed-width strings, the historical padded Maidstone
        # mapping (SOUTH_EAST, ten characters) also participates in dtype
        # promotion. Preserve that interoperability outside the object path.
        native = _resolve(
            (np.array(["LONDON"]), np.array([True])),
            (np.array(["MAIDSTONE"]), np.array([False])),
            (np.array(["ENGLAND"]), np.array([True])),
        )
        np.testing.assert_array_equal(native, ["LONDON"])
        assert native.dtype == np.dtype("<U10")


def test_native_whole_arrays_survive_subset_and_parent_restore():
    """Public Core populations carry whole inputs without UK sparse records."""
    year = 2025
    simulation = Simulation(
        # The constructor's baseline must have the same population IDs as
        # the adopted whole-array world: subsets deliberately fall back
        # when their baseline describes different people or groups.
        situation={
            "age": {year: [40, 40, 40]},
            "would_claim_uc": {year: [False, False, False]},
        }
    )
    native = SimulationBuilder().build_from_variables(
        simulation.tax_benefit_system,
        {
            "age": {year: [40, 40, 40]},
            "country": {year: ["SCOTLAND", "WALES", "ENGLAND"]},
            "region": {year: ["SCOTLAND", "WALES", "LONDON"]},
            "would_claim_uc": {year: [False, False, False]},
        },
    )
    simulation.build_from_populations(native.populations)
    for name in ("region", "country", "local_authority", "brma"):
        assert not getattr(simulation.get_holder(name), _HOLDER_MASKS, ())
    expected = {
        "country": ["SCOTLAND", "WALES", "ENGLAND"],
        "region": ["SCOTLAND", "WALES", "LONDON"],
        "local_authority": ["MAIDSTONE"] * 3,
        "brma": ["LOTHIAN", "CARDIFF", "INNER_SOUTH_EAST_LONDON"],
    }
    for name, values in expected.items():
        np.testing.assert_array_equal(simulation.calculate(name, year), values)
    np.testing.assert_array_equal(simulation.populations["household"].ids, [0, 1, 2])
    np.testing.assert_array_equal(
        simulation.baseline.populations["household"].ids, [0, 1, 2]
    )
    with household_subset(
        simulation, "native_whole_array_control", [True, False, True]
    ) as subset:
        restricted = subset.simulation
        assert restricted is not simulation
        np.testing.assert_array_equal(restricted.populations["household"].ids, [0, 2])
        for name, values in expected.items():
            np.testing.assert_array_equal(
                restricted.calculate(name, year), [values[0], values[2]]
            )
    for name, values in expected.items():
        np.testing.assert_array_equal(simulation.calculate(name, year), values)
    assert "native_whole_array_control" not in simulation.branches
    np.testing.assert_array_equal(
        native.calculate("country", year).decode_to_str(), expected["country"]
    )


def _fact_scan_world(regions):
    """Independent households with only the stated geography input cells."""
    data = {"people": {}, "benunits": {}, "households": {}}
    for index, inputs in enumerate(regions):
        person = f"person{index}"
        data["people"][person] = {"age": {2024: 40}}
        data["benunits"][f"unit{index}"] = {"members": [person]}
        data["households"][f"home{index}"] = {
            "members": [person],
            "region": inputs,
        }
    return Simulation(situation=data)


def test_complete_latest_facts_do_not_read_irrelevant_older_tiers(monkeypatch):
    """A full latest array makes earlier input retrieval unnecessary."""
    simulation = _fact_scan_world(
        [
            {2024: "LONDON", 2026: "WALES", 2028: "SCOTLAND"},
            {2024: "SCOTLAND", 2026: "UNKNOWN", 2028: "LONDON"},
            {2024: "WALES", 2026: "SCOTLAND", 2028: "LONDON"},
        ]
    )
    reads = []
    original = geography.get_stored_input

    def record(holder, source, branch):
        reads.append((branch, str(source)))
        return original(holder, source, branch)

    monkeypatch.setattr(geography, "get_stored_input", record)
    values, found, sources = geography.input_facts(
        simulation.populations["household"], "region", period(2026)
    )
    np.testing.assert_array_equal(values, ["WALES", "UNKNOWN", "SCOTLAND"])
    np.testing.assert_array_equal(found, [True, True, True])
    np.testing.assert_array_equal(sources, ["2026"] * 3)
    assert reads == [(simulation.branch_name, "2026")]


@pytest.mark.parametrize(
    "query, options, expected, present, source",
    [
        (2026, {}, "SCOTLAND", True, "2026"),
        (2026, {"before": True}, "WALES", True, "2024"),
        (2025, {"exact": True}, "LONDON", False, None),
    ],
    ids=("ordinary", "before", "exact-missing"),
)
def test_fact_period_filters_preserve_values_presence_and_source(
    query, options, expected, present, source
):
    simulation = _fact_scan_world([{2024: "WALES", 2026: "SCOTLAND", 2028: "LONDON"}])
    values, found, sources = geography.input_facts(
        simulation.populations["household"], "region", period(query), **options
    )
    np.testing.assert_array_equal(values, [expected])
    np.testing.assert_array_equal(found, [present])
    np.testing.assert_array_equal(sources, [source])


def test_partial_latest_facts_still_read_the_needed_older_cells():
    simulation = _fact_scan_world(
        [
            {2024: "LONDON", 2026: "UNKNOWN"},
            {2024: "WALES", 2028: "LONDON"},
            {2026: "SCOTLAND"},
        ]
    )
    values, found, sources = geography.input_facts(
        simulation.populations["household"], "region", period(2026)
    )
    np.testing.assert_array_equal(values, ["UNKNOWN", "WALES", "SCOTLAND"])
    np.testing.assert_array_equal(found, [True, True, True])
    np.testing.assert_array_equal(sources, ["2026", "2024", "2026"])


def test_same_period_branch_input_precedes_parent_without_mutating_it():
    parent = _fact_scan_world([{2024: "LONDON", 2026: "SCOTLAND"}])
    branch = parent.get_branch("fact_scan", clone_system=True)
    branch.set_input("region", 2026, ["WALES"])
    for world, expected in [(branch, "WALES"), (parent, "SCOTLAND")]:
        values, found, sources = geography.input_facts(
            world.populations["household"], "region", period(2026)
        )
        np.testing.assert_array_equal(values, [expected])
        np.testing.assert_array_equal(found, [True])
        np.testing.assert_array_equal(sources, ["2026"])


def test_complete_later_facts_do_not_skip_prospective_old_override_validation():
    simulation = _fact_scan_world(
        [
            {2024: "LONDON", 2026: "SCOTLAND"},
            {2024: "WALES", 2026: "LONDON"},
        ]
    )
    with pytest.raises(ValueError, match="input length is 1.*2 households"):
        geography.input_facts(
            simulation.populations["household"],
            "region",
            period(2026),
            override=("region", period(2024), ["LONDON"]),
        )


def test_needed_matching_presence_record_rejects_unknown_household_id():
    holder = SimpleNamespace(
        population=SimpleNamespace(ids=np.array(["unknown"]), count=1)
    )
    setattr(holder, _HOLDER_MASKS, ((("default", "2026"), (("known",), (True,))),))
    with pytest.raises(ValueError, match="does not identify household IDs"):
        _cell_mask(holder, "default", period(2026))
