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


def test_overlay_does_not_allocate_unused_source_period_buffers(monkeypatch):
    """A normal warm overlay needs facts, but not their source-date vectors."""
    import policyengine_uk.simulation as simulation_module

    simulation = _fact_scan_world(
        [{2026: "SCOTLAND"}, {2026: "WALES"}, {2026: "LONDON"}]
    )
    expected = ["SCOTLAND", "WALES", "ENGLAND"]
    simulation.set_input("country", 2026, expected)
    np.testing.assert_array_equal(simulation.calculate("country", 2026), expected)
    entered = []
    allocations = []
    active = []
    original_overlay = simulation_module.merge_geography_formula

    def observed_overlay(*args, **kwargs):
        entered.append(args[1].name)
        active.append(True)
        try:
            return original_overlay(*args, **kwargs)
        finally:
            active.pop()

    class ObservedNumpy:
        def __getattr__(self, name):
            return getattr(np, name)

        def full(self, shape, fill_value, *args, **kwargs):
            if active and fill_value is None and kwargs.get("dtype") is object:
                allocations.append(shape)
            return np.full(shape, fill_value, *args, **kwargs)

    monkeypatch.setattr(simulation_module, "merge_geography_formula", observed_overlay)
    monkeypatch.setattr(geography, "np", ObservedNumpy())
    actual = simulation.calculate("country", 2026)
    np.testing.assert_array_equal(actual, expected)
    assert entered == ["country"], "The public calculation must exercise its overlay."
    assert allocations == [], "The overlay discarded allocated source-period vectors."


@pytest.mark.parametrize(
    "query, options, expected, present, sources",
    [
        (
            2026,
            {},
            ["UNKNOWN", "WALES", "SCOTLAND"],
            [True, True, True],
            ["2026", "2024", "2026"],
        ),
        (
            2026,
            {"before": True},
            ["LONDON", "WALES", "LONDON"],
            [True, True, False],
            ["2024", "2024", None],
        ),
        (
            2025,
            {"exact": True},
            ["LONDON", "LONDON", "LONDON"],
            [False, False, False],
            [None, None, None],
        ),
    ],
    ids=("ordinary", "before", "exact-missing"),
)
def test_optional_sources_preserve_sparse_values_and_presence(
    query, options, expected, present, sources
):
    simulation = _fact_scan_world(
        [
            {2024: "LONDON", 2026: "UNKNOWN"},
            {2024: "WALES", 2028: "LONDON"},
            {2026: "SCOTLAND"},
        ]
    )
    population = simulation.populations["household"]
    ordinary = geography.input_facts(population, "region", period(query), **options)
    explicit = geography.input_facts(
        population, "region", period(query), with_sources=True, **options
    )
    omitted = geography.input_facts(
        population, "region", period(query), with_sources=False, **options
    )
    for result in (ordinary, explicit, omitted):
        np.testing.assert_array_equal(result[0], expected)
        np.testing.assert_array_equal(result[1], present)
        assert result[0].dtype == np.dtype(object)
        assert result[1].dtype == np.dtype(bool)
    for result in (ordinary, explicit):
        np.testing.assert_array_equal(result[2], sources)
        assert result[2].dtype == np.dtype(object)
    assert omitted[2] is None
    assert not np.shares_memory(ordinary[0], omitted[0])
    assert not np.shares_memory(ordinary[1], omitted[1])


@pytest.mark.parametrize(
    "replacement, message",
    [
        (["LONDON"], "input length is 1.*2 households"),
        (["NOT_A_REGION", "WALES"], "Invalid value.*NOT_A_REGION"),
    ],
    ids=("bad-length", "bad-enum"),
)
def test_omitting_sources_keeps_older_override_validation(replacement, message):
    simulation = _fact_scan_world(
        [
            {2024: "LONDON", 2026: "SCOTLAND"},
            {2024: "WALES", 2026: "LONDON"},
        ]
    )
    population = simulation.populations["household"]
    with pytest.raises(ValueError, match=message):
        geography.input_facts(
            population,
            "region",
            period(2026),
            override=("region", period(2024), replacement),
            with_sources=False,
        )
    values, present, sources = geography.input_facts(population, "region", period(2026))
    np.testing.assert_array_equal(values, ["SCOTLAND", "LONDON"])
    np.testing.assert_array_equal(present, [True, True])
    np.testing.assert_array_equal(sources, ["2026", "2026"])


def test_overlay_rereads_inputs_after_warning_hook_mutates_input(monkeypatch):
    """A standard warning hook can replace the requested public input."""
    import warnings

    simulation = _fact_scan_world([{2026: "SCOTLAND"}])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.set_input("country", 2026, ["ENGLAND"])
    mutations = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        original_showwarning = warnings.showwarning

        def move_input(message, category, filename, lineno, file=None, line=None):
            if "Contradictory supplied" in str(message) and not mutations:
                mutations.append("country")
                simulation.set_input("country", 2026, ["SCOTLAND"])
            return original_showwarning(message, category, filename, lineno, file, line)

        with monkeypatch.context() as patch:
            patch.setattr(warnings, "showwarning", move_input)
            actual = simulation.calculate("country", 2026)
    assert mutations == ["country"]
    assert len([x for x in caught if "Contradictory supplied" in str(x.message)]) == 1
    np.testing.assert_array_equal(actual, ["SCOTLAND"])
    np.testing.assert_array_equal(simulation.calculate("country", 2026), ["SCOTLAND"])
    np.testing.assert_array_equal(simulation.calculate("region", 2026), ["SCOTLAND"])


def test_omitting_sources_preserves_custom_decoder_side_effects(monkeypatch):
    simulation = _fact_scan_world([{2026: "WALES"}, {2026: "UNKNOWN"}])
    population = simulation.populations["household"]
    holder = population.get_holder("region")
    array = geography.get_stored_input(holder, period(2026), simulation.branch_name)
    original_decoder = array.decode_to_str
    calls = []

    def custom_decoder():
        calls.append("decoded")
        return original_decoder()

    monkeypatch.setattr(array, "decode_to_str", custom_decoder)
    ordinary = geography.input_facts(population, "region", period(2026))
    omitted = geography.input_facts(
        population, "region", period(2026), with_sources=False
    )
    for result in (ordinary, omitted):
        np.testing.assert_array_equal(result[0], ["WALES", "UNKNOWN"])
        np.testing.assert_array_equal(result[1], [True, True])
    np.testing.assert_array_equal(ordinary[2], ["2026", "2026"])
    assert omitted[2] is None
    assert calls == ["decoded", "decoded"]


@pytest.mark.parametrize("decoded_dtype", [object, "U16"])
@pytest.mark.parametrize("with_sources", [False, True])
def test_full_native_decode_keeps_target_dtype_identity_and_ownership(
    monkeypatch, decoded_dtype, with_sources
):
    class Label(str):
        pass

    label = Label("SCOTLAND")
    decoded = np.array([label, "WALES"], dtype=decoded_dtype)
    simulation = _fact_scan_world([{2026: "SCOTLAND"}, {2026: "WALES"}])
    targets, calls = [], []
    original_full = np.full

    def full(shape, fill, *args, **kwargs):
        result = original_full(shape, fill, *args, **kwargs)
        if fill == "LONDON" and result.dtype == object:
            targets.append(result)
        return result

    def names(*args):
        calls.append("decode")
        return decoded

    monkeypatch.setattr(geography.np, "full", full)
    monkeypatch.setattr(geography, "_names", names)
    values, found, sources = geography.input_facts(
        simulation.populations["household"],
        "region",
        period(2026),
        with_sources=with_sources,
    )
    assert calls == ["decode"]
    assert len(targets) == 1 and values is targets[0]
    assert values is not decoded and values.dtype == np.dtype(object)
    assert not np.shares_memory(values, decoded)
    np.testing.assert_array_equal(values, ["SCOTLAND", "WALES"])
    np.testing.assert_array_equal(found, [True, True])
    if decoded_dtype is object:
        assert values[0] is label
    if with_sources:
        np.testing.assert_array_equal(sources, ["2026", "2026"])
    else:
        assert sources is None
    values[0] = "LONDON"
    assert decoded[0] == "SCOTLAND"


def test_sparse_decoder_keeps_boolean_indexing_and_default_cells(monkeypatch):
    simulation = _fact_scan_world([{2026: "SCOTLAND"}, {2026: "WALES"}])
    events = []

    class Indexed(np.ndarray):
        def __getitem__(self, key):
            events.append(("index", key.copy()))
            return super().__getitem__(key)

    decoded = np.array(["SCOTLAND", "WALES"], dtype=object).view(Indexed)

    def names(*args):
        events.append(("decode", None))
        return decoded

    monkeypatch.setattr(geography, "_names", names)
    monkeypatch.setattr(geography, "_cell_mask", lambda *args: np.array([True, False]))
    values, found, sources = geography.input_facts(
        simulation.populations["household"], "region", period(2026)
    )
    assert [event[0] for event in events] == ["decode", "index"]
    np.testing.assert_array_equal(events[1][1], [True, False])
    np.testing.assert_array_equal(values, ["SCOTLAND", "LONDON"])
    np.testing.assert_array_equal(found, [True, False])
    np.testing.assert_array_equal(sources, ["2026", None])


@pytest.mark.parametrize("view", [False, True])
def test_temporary_decoder_weakref_runs_before_target_assignment(monkeypatch, view):
    import weakref

    simulation = _fact_scan_world([{2026: "SCOTLAND"}, {2026: "WALES"}])
    target, references, events = {}, [], []
    original_full = np.full

    def full(shape, fill, *args, **kwargs):
        result = original_full(shape, fill, *args, **kwargs)
        if fill == "LONDON" and result.dtype == object:
            target["values"] = result
        return result

    def released(reference):
        events.append("released")
        target["values"][:] = "UNKNOWN"

    def names(*args):
        events.append("decode")
        owner = np.array(["SCOTLAND", "WALES"], dtype=object)
        references.append(weakref.ref(owner, released))
        return owner.view() if view else owner

    monkeypatch.setattr(geography.np, "full", full)
    monkeypatch.setattr(geography, "_names", names)
    values, found, sources = geography.input_facts(
        simulation.populations["household"], "region", period(2026)
    )
    assert events == ["decode", "released"]
    assert values is target["values"]
    np.testing.assert_array_equal(values, ["SCOTLAND", "WALES"])
    np.testing.assert_array_equal(found, [True, True])
    np.testing.assert_array_equal(sources, ["2026", "2026"])


def test_custom_decoder_getitem_error_retains_exception_identity(monkeypatch):
    simulation = _fact_scan_world([{2026: "SCOTLAND"}])
    marker = RuntimeError("custom decoder index")
    events = []

    class Indexed(np.ndarray):
        def __getitem__(self, key):
            events.append("index")
            raise marker

    def names(*args):
        events.append("decode")
        return np.array(["SCOTLAND"], dtype=object).view(Indexed)

    monkeypatch.setattr(geography, "_names", names)
    with pytest.raises(RuntimeError) as caught:
        geography.input_facts(
            simulation.populations["household"], "region", period(2026)
        )
    assert caught.value is marker
    assert events == ["decode", "index"]


def test_custom_target_assignment_error_keeps_temporary_release_order(monkeypatch):
    import weakref

    simulation = _fact_scan_world([{2026: "SCOTLAND"}])
    marker = RuntimeError("custom target assignment")
    events, references = [], []
    original_full = np.full

    class Target(np.ndarray):
        def __setitem__(self, key, value):
            events.append("assign")
            assert type(key) is np.ndarray and key.dtype == bool
            raise marker

    def full(shape, fill, *args, **kwargs):
        result = original_full(shape, fill, *args, **kwargs)
        return (
            result.view(Target)
            if fill == "LONDON" and result.dtype == object
            else result
        )

    def names(*args):
        decoded = np.array(["SCOTLAND"], dtype=object)
        references.append(
            weakref.ref(decoded, lambda reference: events.append("released"))
        )
        return decoded

    monkeypatch.setattr(geography.np, "full", full)
    monkeypatch.setattr(geography, "_names", names)
    with pytest.raises(RuntimeError) as caught:
        geography.input_facts(
            simulation.populations["household"], "region", period(2026)
        )
    assert caught.value is marker
    assert events == ["released", "assign"]


@pytest.mark.parametrize(
    "decoded, error",
    [
        (np.array(1, dtype=object), IndexError),
        (np.array([["SCOTLAND"]], dtype=object), TypeError),
    ],
)
def test_malformed_decoder_shapes_keep_original_index_errors(
    monkeypatch, decoded, error
):
    # Bind each oracle to the exact pre-change NumPy assignment, including
    # the distinction between source-index and target-assignment failures.
    old_values = np.full(1, "LONDON", dtype=object)
    old_take = np.ones(1, dtype=bool)
    with pytest.raises(error):
        old_values[old_take] = decoded[old_take]
    simulation = _fact_scan_world([{2026: "SCOTLAND"}])
    monkeypatch.setattr(geography, "_names", lambda *args: decoded)
    with pytest.raises(error):
        geography.input_facts(
            simulation.populations["household"], "region", period(2026)
        )


def test_native_numeric_decoder_keeps_original_object_conversion(monkeypatch):
    simulation = _fact_scan_world([{2026: "SCOTLAND"}, {2026: "WALES"}])
    decoded = np.array([1, 2], dtype=np.int16)
    monkeypatch.setattr(geography, "_names", lambda *args: decoded)
    values, found, _ = geography.input_facts(
        simulation.populations["household"], "region", period(2026)
    )
    assert values.dtype == np.dtype(object)
    np.testing.assert_array_equal(values, [1, 2])
    np.testing.assert_array_equal(found, [True, True])


@pytest.mark.parametrize("owner_kind", ["object", "structured"])
def test_decoder_owner_payload_destruction_keeps_original_assignment_order(
    monkeypatch, owner_kind
):
    simulation = _fact_scan_world([{2026: "SCOTLAND"}])
    target, events = {}, []
    original_full = np.full

    class Payload:
        def __del__(self):
            events.append("payload released")
            target["values"][:] = "UNKNOWN"

    def full(shape, fill, *args, **kwargs):
        result = original_full(shape, fill, *args, **kwargs)
        if fill == "LONDON" and result.dtype == object:
            target["values"] = result
        return result

    def names(*args):
        if owner_kind == "object":
            owner = np.array(["SCOTLAND", Payload()], dtype=object)
            return owner[:1]
        owner = np.empty(1, dtype=[("label", "U16"), ("payload", object)])
        owner["label"] = "SCOTLAND"
        owner["payload"][0] = Payload()
        return owner["label"]

    monkeypatch.setattr(geography.np, "full", full)
    monkeypatch.setattr(geography, "_names", names)
    values, found, sources = geography.input_facts(
        simulation.populations["household"], "region", period(2026)
    )
    assert events == ["payload released"]
    assert values is target["values"]
    np.testing.assert_array_equal(values, ["SCOTLAND"])
    np.testing.assert_array_equal(found, [True])
    np.testing.assert_array_equal(sources, ["2026"])


def test_read_only_native_target_releases_decoded_payload_before_error_handler(
    monkeypatch,
):
    simulation = _fact_scan_world([{2026: "SCOTLAND"}])
    events = []
    original_full = np.full

    class Payload:
        def __del__(self):
            events.append("released")

    def full(shape, fill, *args, **kwargs):
        result = original_full(shape, fill, *args, **kwargs)
        if fill == "LONDON" and result.dtype == object:
            result.setflags(write=False)
        return result

    monkeypatch.setattr(geography.np, "full", full)
    monkeypatch.setattr(
        geography, "_names", lambda *args: np.array([Payload()], dtype=object)
    )
    with pytest.raises(ValueError, match="read-only") as caught:
        geography.input_facts(
            simulation.populations["household"], "region", period(2026)
        )
    assert "read-only" in str(caught.value)
    assert events == ["released"]


def _native_overlay_world():
    """Whole native Core inputs, one adult per coherent Scottish/Welsh home."""
    inputs = {
        "age": {2026: [40, 40]},
        "would_claim_uc": {2026: [False, False]},
        "region": {2026: ["SCOTLAND", "WALES"]},
        "country": {2026: ["SCOTLAND", "WALES"]},
        "local_authority": {2026: ["CITY_OF_EDINBURGH", "CARDIFF"]},
        "brma": {2026: ["LOTHIAN", "CARDIFF"]},
    }
    simulation = Simulation(
        situation={key: inputs[key] for key in ("age", "would_claim_uc")}
    )
    native = SimulationBuilder().build_from_variables(
        simulation.tax_benefit_system, inputs
    )
    simulation.build_from_populations(native.populations)
    return simulation


@pytest.mark.parametrize(
    "name, expected",
    [
        ("country", ["SCOTLAND", "WALES"]),
        ("region", ["SCOTLAND", "WALES"]),
        ("local_authority", ["CITY_OF_EDINBURGH", "CARDIFF"]),
        ("brma", ["LOTHIAN", "CARDIFF"]),
    ],
)
def test_public_whole_input_overlay_returns_fresh_encoded_storage(
    monkeypatch, name, expected
):
    """The real overlay may copy native inputs, but must never return aliases."""
    import policyengine_uk.simulation as simulation_module
    from policyengine_core.enums import EnumArray

    simulation = _native_overlay_world()
    holder = simulation.get_holder(name)
    stored = geography.get_stored_input(holder, period(2026), simulation.branch_name)
    original_indices = np.asarray(stored).copy()
    entered = []
    original_overlay = simulation_module.merge_geography_formula

    def forbidden_instance_copy(*args, **kwargs):
        raise AssertionError("The overlay must not dispatch an input's copy override.")

    def observe(*args, **kwargs):
        result = original_overlay(*args, **kwargs)
        if args[1].name == name:
            entered.append((args[3], result))
        return result

    monkeypatch.setattr(stored, "copy", forbidden_instance_copy)
    monkeypatch.setattr(simulation_module, "merge_geography_formula", observe)
    first_public = simulation.calculate(name, 2026)
    np.testing.assert_array_equal(first_public, expected)
    assert len(entered) == 1
    native, encoded = entered[0]
    assert (
        type(encoded) is EnumArray and encoded.possible_values is stored.possible_values
    )
    assert encoded.shape == stored.shape == (2,) and encoded.dtype == np.dtype("int16")
    assert not np.shares_memory(encoded, stored)
    assert not np.shares_memory(encoded, native)
    encoded[0] = original_indices[1]
    np.testing.assert_array_equal(np.asarray(stored), original_indices)
    second_public = simulation.calculate(name, 2026)
    np.testing.assert_array_equal(second_public, expected)
    assert not np.shares_memory(entered[0][1], entered[1][1])
    assert first_public.dtype == second_public.dtype


@pytest.mark.parametrize("kind", ["instance", "subclass", "rebound-native"])
def test_public_overlay_preserves_custom_stored_decoder(monkeypatch, kind):
    """The requested field retains its declared custom decoder output."""
    import warnings
    from policyengine_core.enums import EnumArray

    simulation = _native_overlay_world()
    holder = simulation.get_holder("country")
    stored = geography.get_stored_input(holder, period(2026), simulation.branch_name)
    expected = ["WALES", "SCOTLAND"]

    def decode():
        return np.array(expected)

    if kind == "instance":
        monkeypatch.setattr(stored, "decode_to_str", decode)
    elif kind == "subclass":

        class CustomDecodedInput(EnumArray):
            def decode_to_str(self):
                return decode()

        holder._set(
            period(2026),
            stored.view(CustomDecodedInput),
            branch_name=simulation.branch_name,
            is_input=True,
        )
    else:
        other = stored.possible_values.encode(np.array(expected))
        monkeypatch.setattr(stored, "decode_to_str", other.decode_to_str)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        actual = simulation.calculate("country", 2026)
    np.testing.assert_array_equal(actual, expected)


def test_public_overlay_retains_custom_encoder_exception_identity(monkeypatch):
    from policyengine_core.enums import EnumArray

    simulation = _native_overlay_world()
    possible = simulation.get_holder("country").variable.possible_values
    original_encode = possible.encode
    marker = RuntimeError("custom geography name encoder")
    calls = []

    def encode(cls, values):
        if not isinstance(values, EnumArray) and np.asarray(values).dtype == object:
            calls.append("encode names")
            raise marker
        return original_encode(values)

    monkeypatch.setattr(possible, "encode", classmethod(encode))
    with pytest.raises(RuntimeError) as caught:
        simulation.calculate("country", 2026)
    assert caught.value is marker
    assert calls == ["encode names"]


def test_public_overlay_retains_mutated_native_sorted_lookup():
    """An unchanged method may return changed cached lookup array contents."""
    simulation = _native_overlay_world()
    possible = simulation.get_holder("country").variable.possible_values
    names, indices = possible._get_sorted_lookup_arrays()
    original_indices = indices.copy()
    left = int(np.flatnonzero(names == "SCOTLAND")[0])
    right = int(np.flatnonzero(names == "WALES")[0])
    try:
        indices[left], indices[right] = original_indices[right], original_indices[left]
        # These are the native encoder's declared lookup results, not a
        # proposed implementation helper or a second policy computation.
        np.testing.assert_array_equal(
            simulation.calculate("country", 2026), ["WALES", "SCOTLAND"]
        )
    finally:
        indices[:] = original_indices


@pytest.mark.parametrize("schema", ["dense", "sparse"])
def test_public_overlay_respects_alternate_enum_schema(monkeypatch, schema):
    import warnings
    from policyengine_core.enums import Enum, EnumArray

    class DenseGeography(Enum):
        EAST = "east"
        WEST = "west"

    class SparseGeography(Enum):
        def __init__(self, label, index):
            self.index = index

        EAST = ("east", 2)
        WEST = ("west", 7)

    possible = DenseGeography if schema == "dense" else SparseGeography
    simulation = _native_overlay_world()
    holder = simulation.get_holder("country")
    monkeypatch.setattr(holder.variable, "possible_values", possible)
    encoded = EnumArray(
        np.array([item.index for item in possible], dtype="int16"), possible
    )
    holder._set(
        period(2026), encoded, branch_name=simulation.branch_name, is_input=True
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        actual = simulation.calculate("country", 2026)
    np.testing.assert_array_equal(actual, ["EAST", "WEST"])
    assert actual.dtype == encoded.decode_to_str().dtype


@pytest.mark.parametrize("bad_index", [-1, 30000])
def test_public_overlay_keeps_invalid_native_index_encode_error(bad_index):
    import warnings

    simulation = _native_overlay_world()
    holder = simulation.get_holder("country")
    stored = geography.get_stored_input(holder, period(2026), simulation.branch_name)
    stored[0] = bad_index
    # Already encoded invalid indices decode as lowercase unknown in Core;
    # the existing overlay's final native name encoding then rejects it.
    names = stored.decode_to_str().astype(object)
    with pytest.raises(ValueError) as expected:
        holder.variable.possible_values.encode(names)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(ValueError) as actual:
            simulation.calculate("country", 2026)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize(
    "tier", ["partial", "parent-only", "older-only", "model-written", "older-child"]
)
def test_public_overlay_keeps_requested_field_fallback_for_noncurrent_tiers(tier):
    """Public outputs retain sparse, parent, carried and model-value fallback."""
    import warnings

    simulation = _native_overlay_world()
    if tier == "partial":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            simulation.set_input("country", 2026, ["SCOTLAND", "ENGLAND"])
        geography.set_cell_mask(simulation, "country", period(2026), [True, False])
    elif tier in {"parent-only", "older-child"}:
        simulation = simulation.get_branch("overlay_fallback", clone_system=True)
        if tier == "older-child":
            simulation.set_input("country", 2024, ["ENGLAND", "ENGLAND"])
    elif tier == "older-only":
        simulation.get_holder("country").delete_arrays(
            period(2026), simulation.branch_name
        )
        simulation.set_input("country", 2024, ["ENGLAND", "ENGLAND"])
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            simulation.set_input("country", 2026, ["ENGLAND", "ENGLAND"])
        stored = geography.get_stored_input(
            simulation.get_holder("country"), period(2026), simulation.branch_name
        )
        # The scenario/model-value storage record excludes this current
        # array from genuine supplied inputs; preserve that read contract.
        simulation._model_values = {
            ("country", simulation.branch_name, period(2026)): np.asarray(stored).copy()
        }
    np.testing.assert_array_equal(
        simulation.calculate("country", 2026), ["SCOTLAND", "WALES"]
    )


def test_public_overlay_keeps_larger_competing_period_selection():
    """A longer genuine region tier with the same start wins the old ordering."""
    import warnings

    simulation = _native_overlay_world()
    # Omit the helper's country declaration to isolate region source ordering.
    # Same-period known-nation conflicts have separate public regressions.
    simulation.delete_arrays("country", period(2026))
    assert "country__2026" not in simulation.to_input_dataframe()
    holder = simulation.get_holder("region")
    exact = geography.get_stored_input(holder, period(2026), simulation.branch_name)
    before = np.asarray(exact).copy()
    holder._set(
        period("year:2026:2"),
        holder.variable.possible_values.encode(np.array(["WALES", "SCOTLAND"])),
        branch_name=simulation.branch_name,
        is_input=True,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        actual = simulation.calculate("region", 2026)
    np.testing.assert_array_equal(actual, ["WALES", "SCOTLAND"])
    np.testing.assert_array_equal(np.asarray(exact), before)


@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "mutation",
    ["indices", "names", "replacement", "rebound_lookup", "rebound_encoder"],
)
def test_public_native_copy_metadata_observes_live_codec_changes(
    monkeypatch, warm, mutation
):
    """A primed static reference never certifies mutable live codec tables."""
    from policyengine_core.enums import Enum

    simulation = _native_overlay_world()
    holder = simulation.get_holder("country")
    # Each row has a distinct dense schema, so cold does not depend on test order.
    members = {
        "ENGLAND": "England",
        "NORTHERN_IRELAND": "Northern Ireland",
        "SCOTLAND": "Scotland",
        "WALES": "Wales",
        "UNKNOWN": "Unknown",
        f"SCHEMA_{mutation.upper()}_{'WARM' if warm else 'COLD'}": "Schema marker",
    }
    possible = Enum("RevisionCountry", members)
    monkeypatch.setattr(holder.variable, "possible_values", possible)
    simulation.set_input("country", 2026, ["SCOTLAND", "WALES"])
    if warm:
        np.testing.assert_array_equal(
            simulation.calculate("country", 2026), ["SCOTLAND", "WALES"]
        )

    table_owner = possible
    if mutation in {"rebound_lookup", "rebound_encoder"}:
        table_owner = Enum("ReboundRevisionCountry", members)
    names, indices = table_owner._get_sorted_lookup_arrays()
    original_names, original_indices = names.copy(), indices.copy()
    left = int(np.flatnonzero(names == "SCOTLAND")[0])
    right = int(np.flatnonzero(names == "WALES")[0])
    try:
        with monkeypatch.context() as patch:
            if mutation == "names":
                names[left] = "SCOTLAND_CHANGED"
            elif mutation == "replacement":
                replacement_names = names.copy()
                replacement_indices = indices.copy()
                replacement_indices[left], replacement_indices[right] = (
                    original_indices[right],
                    original_indices[left],
                )

                def replacement(cls):
                    return replacement_names, replacement_indices

                patch.setattr(
                    possible, "_get_sorted_lookup_arrays", classmethod(replacement)
                )
            else:
                indices[left], indices[right] = (
                    original_indices[right],
                    original_indices[left],
                )
                if mutation == "rebound_lookup":
                    patch.setattr(
                        possible,
                        "_get_sorted_lookup_arrays",
                        table_owner._get_sorted_lookup_arrays,
                    )
                elif mutation == "rebound_encoder":
                    patch.setattr(possible, "encode", table_owner.encode)
            if mutation == "names":
                # Core's native encoder supplies the public error contract.
                with pytest.raises(ValueError) as expected:
                    possible.encode(np.array(["SCOTLAND", "WALES"], dtype=object))
                with pytest.raises(ValueError) as actual:
                    simulation.calculate("country", 2026)
                assert str(actual.value) == str(expected.value)
            else:
                np.testing.assert_array_equal(
                    simulation.calculate("country", 2026), ["WALES", "SCOTLAND"]
                )
    finally:
        names[:] = original_names
        indices[:] = original_indices
    np.testing.assert_array_equal(
        simulation.calculate("country", 2026), ["SCOTLAND", "WALES"]
    )


@pytest.mark.parametrize("whole_native", [True, False])
def test_public_overlay_never_reinstates_a_region_superseded_by_a_newer_council(
    whole_native,
):
    if whole_native:
        simulation = Simulation(
            situation={
                "age": {2024: [40, 40]},
                "region": {2024: ["LONDON", "WALES"]},
                "local_authority": {2026: ["CITY_OF_EDINBURGH", "CARDIFF"]},
            }
        )
    else:
        simulation = Simulation(
            situation={
                "people": {"a": {"age": {2024: 40}}, "b": {"age": {2024: 40}}},
                "benunits": {"a": {"members": ["a"]}, "b": {"members": ["b"]}},
                "households": {
                    "a": {
                        "members": ["a"],
                        "region": {2024: "LONDON"},
                        "local_authority": {2026: "CITY_OF_EDINBURGH"},
                    },
                    "b": {"members": ["b"], "region": {2024: "WALES"}},
                },
            }
        )
    before = simulation.to_input_dataframe()
    possible = simulation.get_holder("region").variable.possible_values
    np.testing.assert_array_equal(
        before["region__2024"].to_numpy(),
        np.asarray(possible.encode(np.array(["LONDON", "WALES"]))),
    )
    first = simulation.calculate("region", 2026)
    np.testing.assert_array_equal(first, ["SCOTLAND", "WALES"])
    # Inspect storage before a later read can replace any cached arrays.
    cached_periods = simulation.get_known_periods("region")
    assert cached_periods
    assert period(2024) in cached_periods
    for cached_period in cached_periods:
        cached = simulation.get_array("region", cached_period)
        assert cached is not None
        assert not np.shares_memory(first, cached)
    second = simulation.calculate("region", 2026)
    np.testing.assert_array_equal(second, ["SCOTLAND", "WALES"])
    assert not np.shares_memory(first, second)
    cached_periods_after = simulation.get_known_periods("region")
    assert cached_periods_after
    assert period(2024) in cached_periods_after
    for cached_period in cached_periods_after:
        cached = simulation.get_array("region", cached_period)
        assert cached is not None
        assert not np.shares_memory(first, cached)
        assert not np.shares_memory(second, cached)
    np.testing.assert_array_equal(
        simulation.calculate("country", 2026), ["SCOTLAND", "WALES"]
    )
    np.testing.assert_array_equal(
        simulation.to_input_dataframe()["region__2024"].to_numpy(),
        np.asarray(possible.encode(np.array(["LONDON", "WALES"]))),
    )
    assert "region__2026" not in simulation.to_input_dataframe()


@pytest.mark.parametrize("queried", [2024, 2026])
@pytest.mark.parametrize(
    "longer_field,expected", [("local_authority", "SCOTLAND"), ("region", "LONDON")]
)
def test_public_cross_field_source_order_uses_the_source_stop_after_an_equal_start(
    longer_field, expected, queried
):
    import warnings

    simulation = Simulation(situation={"age": {2024: 40}})
    sources = {
        "region": "year:2024:3" if longer_field == "region" else 2024,
        "local_authority": "year:2024:3" if longer_field == "local_authority" else 2024,
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.set_input("region", sources["region"], ["LONDON"])
        simulation.set_input(
            "local_authority", sources["local_authority"], ["CITY_OF_EDINBURGH"]
        )
    np.testing.assert_array_equal(simulation.calculate("region", queried), [expected])
    np.testing.assert_array_equal(
        simulation.calculate("country", queried),
        ["SCOTLAND" if expected == "SCOTLAND" else "ENGLAND"],
    )
    if longer_field == "region":
        with pytest.raises(ValueError, match="(?i)council|local_authority"):
            simulation.calculate("local_authority", queried)
    else:
        np.testing.assert_array_equal(
            simulation.calculate("local_authority", queried), ["CITY_OF_EDINBURGH"]
        )
    exported = simulation.to_input_dataframe()
    for name, label in [("region", "LONDON"), ("local_authority", "CITY_OF_EDINBURGH")]:
        possible = simulation.get_holder(name).variable.possible_values
        column = name + "__" + str(period(sources[name]))
        np.testing.assert_array_equal(
            exported[column].to_numpy(), np.asarray(possible.encode(np.array([label])))
        )


@pytest.mark.parametrize(
    "requested,expected", [(None, "SCOTLAND"), (2024, "SCOTLAND"), (2026, "LONDON")]
)
def test_snapshot_table_country_uses_the_requested_year_and_default_horizon(
    requested, expected
):
    from copy import deepcopy
    import pandas as pd

    frame = pd.DataFrame({"household_id": [1001], "country": ["SCOTLAND"]})
    frame.attrs["policyengine_uk.geography_input_masks"] = {
        "rows": ((0, 1001),),
        "masks": (("country", ((1001, True),)),),
        "horizon": "2024",
        "history": (),
    }
    before, metadata = frame.copy(deep=True), deepcopy(frame.attrs)
    actual = (
        geography.region_from_table(frame)
        if requested is None
        else geography.region_from_table(frame, period=requested)
    )
    np.testing.assert_array_equal(actual, [expected])
    pd.testing.assert_frame_equal(frame, before)
    assert frame.attrs == metadata


@pytest.mark.parametrize("country_supplied", [True, False])
def test_country_evaluates_a_custom_region_view_only_when_required(
    monkeypatch, country_supplied
):
    """The same view is unused for supplied country and required by its formula."""
    simulation = _native_overlay_world()
    if not country_supplied:
        simulation.delete_arrays("country", period(2026))
    stored = geography.get_stored_input(
        simulation.get_holder("region"), period(2026), simulation.branch_name
    )
    marker = RuntimeError("custom region view")

    def decode():
        raise marker

    monkeypatch.setattr(stored, "decode_to_str", decode)
    if country_supplied:
        np.testing.assert_array_equal(
            simulation.calculate("country", 2026), ["SCOTLAND", "WALES"]
        )
    else:
        with pytest.raises(RuntimeError) as caught:
            simulation.calculate("country", 2026)
        assert caught.value is marker


def test_requested_country_decoder_error_keeps_its_identity(monkeypatch):
    simulation = _native_overlay_world()
    stored = geography.get_stored_input(
        simulation.get_holder("country"), period(2026), simulation.branch_name
    )
    marker = RuntimeError("requested country view")

    def decode():
        raise marker

    monkeypatch.setattr(stored, "decode_to_str", decode)
    with pytest.raises(RuntimeError) as caught:
        simulation.calculate("country", 2026)
    assert caught.value is marker
