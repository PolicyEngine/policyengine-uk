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
