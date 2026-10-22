"""``Simulation.subsample`` keeps a weighted sample of a dataset's households.

Before, the method was inherited from policyengine-core and raised
``TypeError``: it rebuilds through ``build_from_dataset()`` with no arguments,
and the UK builder needs the dataset. The UK method subsamples the
simulation's populations, its baseline and its dataset together.

Invariants, for every dataset, sample size ``n``, seed, sampling period and
``quantize_weights``:

1. Size: between 1 and ``n`` households are kept, each with a positive weight
   in the sampling period.
2. Weight totals: the total household weight of every year is unchanged, to
   float32 precision, and so is the total of every other supplied weight over
   its own entity.
3. Quantized weights: with ``quantize_weights`` (the default), a household's
   weight is its number of draws times the year's total over the draws of
   households with a positive weight that year: a whole multiple of
   total / ``n`` in the sampling year, and in any year where every drawn
   household has a positive weight, with the multiples summing to ``n``.
   Without it, a household's weight is proportional to its old weight times a
   whole number of draws. Either way a zero weight stays zero, in every year.
4. Links: a kept household or benefit unit has exactly the people it had, a
   kept person keeps their household and benefit unit, and no other record is
   kept. This holds for identifiers that 32-bit floats cannot tell apart, and
   whatever the stored ``person_household_id`` and ``person_benunit_id``
   inputs hold.
5. Inputs: every supplied value other than a weight is unchanged for the kept
   records, in every period, and the subsample supplies the same variables
   and periods as before. Calculated values are not kept.
6. Determinism: the same seed keeps the same households with the same weights.
7. Baseline: the baseline is replaced with a copy that holds the same
   households and weights and keeps its own policy. The baseline held before
   is unchanged, so subsampling a clone leaves the source simulation and its
   baseline as they were.
8. Dataset (differential): ``dataset`` holds the same records as the
   populations, from the rows of the dataset the simulation was built from,
   with weights rescaled in the same way. For a simulation whose inputs are
   all in its dataset, a simulation built from that dataset gives the same
   results as the subsampled simulation. Intended: an input the dataset does
   not hold stays out of it, as it was out of the dataset before
   subsampling. That is an input set with ``set_input`` after the build, or
   one for a part of a year, which a DataFrame can give and a dataset of
   whole years cannot hold.
9. Unbiasedness: over many seeds, a household's mean quantized weight in the
   sampling period is its old weight. Intended exceptions: in another period,
   the mean is the household's share of the sampling period's total times
   that period's total, which is its old weight only if its share is the same
   in both periods; and unquantized weights keep the total exactly, so they
   are a ratio estimate, whose mean is off by a few per cent in a small
   sample and closes on the old weight as the sample grows.
10. Trace and inputs: the tracer starts again, and a supplied input stored on
    disk is kept, not a value calculated later and cached over it in memory.
11. Model values and origins: a value the model stored as its own
    (``set_model_value``, as the Universal Credit health element reform does
    for every simulation) stays the model's, not supplied, and the record of
    where each capital gains input came from is unchanged.

The properties are generated for datasets of one year, which the model
projects, and of several years whose weights change differently from
household to household.

Intended exceptions: a simulation built from a situation, one given no
household weights or a negative one, a branch, and a baseline holding other
households raise ``ValueError`` and are left unchanged.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.data_storage import OnDiskStorage
from policyengine_core.periods import period as period_
from policyengine_core.tracers import FullTracer

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.utils.subsample import (
    WEIGHT_VARIABLES,
    draw_household_counts,
    rescale_weights,
    subsample_dataset,
)
from policyengine_uk.utils.supplied_inputs import (
    is_model_value,
    set_model_value,
    stored_supplied_value,
    supplied_input,
    supplied_input_arrays,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = range(2025, 2031)
# Neighbouring identifiers of the size the UK datasets use. As 32-bit floats,
# identifiers this large are exact only at multiples of 64.
FIRST_HOUSEHOLD_ID = 900_000_001
FIRST_BENUNIT_ID = 906_000_001
FIRST_PERSON_ID = 967_000_001
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
REGIONS = ["LONDON", "WALES", "SCOTLAND", "NORTH_EAST"]

# Six households: (weight, people in each benefit unit).
HOUSEHOLDS = [
    (100.0, [1, 1]),
    (200.0, [1]),
    (300.0, [2, 2]),
    (400.0, [1]),
    (500.0, [1, 1]),
    (600.0, [2]),
]


def dataset(households=HOUSEHOLDS, year=2025, weights=True) -> UKSingleYearDataset:
    """A dataset of ``households``, each a weight and the number of people in
    each of its benefit units."""
    people, benunits, rows = [], [], []
    for index, (weight, units) in enumerate(households):
        household_id = FIRST_HOUSEHOLD_ID + index
        rows.append(
            {
                "household_id": household_id,
                "household_weight": weight,
                "region": REGIONS[index % len(REGIONS)],
                "rent": 0.0,
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": 1_000.0 + index,
            }
        )
        for size in units:
            benunit_id = FIRST_BENUNIT_ID + len(benunits)
            benunits.append({"benunit_id": benunit_id})
            for _ in range(size):
                people.append(
                    {
                        "person_id": FIRST_PERSON_ID + len(people),
                        "person_benunit_id": benunit_id,
                        "person_household_id": household_id,
                        "age": 25 + 3 * len(people),
                        "employment_income": 9_000.0 * (1 + len(people) % 7),
                    }
                )
    household = pd.DataFrame(rows)
    if not weights:
        household = household.drop(columns="household_weight")
    return UKSingleYearDataset(
        person=pd.DataFrame(people),
        benunit=pd.DataFrame(benunits),
        household=household,
        fiscal_year=year,
    )


def values(simulation, variable, period) -> np.ndarray:
    return np.asarray(simulation.calculate(variable, period))


def ids(simulation, entity) -> list:
    return np.asarray(simulation.populations[entity].ids).tolist()


def members(simulation, entity) -> dict:
    """The people in each ``entity``, by its identifier, from the populations."""
    population = simulation.populations[entity]
    groups = np.asarray(population.ids)[population.members_entity_id]
    members_by_group = {group: set() for group in ids(simulation, entity)}
    for person, group in zip(ids(simulation, "person"), groups.tolist()):
        members_by_group[group].add(person)
    return members_by_group


def by_id(simulation, variable, period) -> dict:
    entity = simulation.tax_benefit_system.get_variable(variable).entity.key
    return dict(zip(ids(simulation, entity), values(simulation, variable, period)))


def weights_by_id(simulation, period) -> dict:
    return by_id(simulation, "household_weight", period)


def supplied(simulation) -> set:
    """The variables and periods the simulation holds supplied values for."""
    return {
        (name, str(period)) for name, period, _ in supplied_input_arrays(simulation)
    }


# The reported failure.


def test_subsample_runs_on_a_dataset_simulation():
    simulation = Microsimulation(dataset=dataset())
    total = values(simulation, "household_weight", 2026).sum()

    result = simulation.subsample(n=4, seed=0, time_period=2026)

    assert result is simulation
    assert 1 <= len(ids(simulation, "household")) <= 4
    assert values(simulation, "household_weight", 2026).sum() == pytest.approx(
        total, rel=1e-5
    )
    assert np.isfinite(values(simulation, "household_net_income", 2026)).all()


def test_subsample_is_the_uk_method_not_policyengine_cores():
    """policyengine-core's method ends in ``build_from_dataset()``, which the
    UK builder cannot answer, so the UK classes must not inherit it."""
    assert "subsample" in vars(Simulation)
    assert Microsimulation.subsample is Simulation.subsample


# Links.


def test_identifiers_beyond_float32_precision_keep_their_households():
    simulation = Microsimulation(dataset=dataset())
    households = members(simulation, "household")
    benunits = members(simulation, "benunit")

    simulation.subsample(n=5, seed=3, time_period=2025)

    kept = ids(simulation, "household")
    assert 1 < len(kept) <= 5
    assert members(simulation, "household") == {
        household: households[household] for household in kept
    }
    kept_people = set(ids(simulation, "person"))
    assert members(simulation, "benunit") == {
        benunit: people for benunit, people in benunits.items() if people <= kept_people
    }
    assert kept_people == set().union(*(households[household] for household in kept))
    assert values(simulation, "household_id", 2025).tolist() == kept


def test_memberships_come_from_the_populations_not_the_stored_identifiers():
    simulation = Microsimulation(dataset=dataset())
    households = members(simulation, "household")
    benunits = members(simulation, "benunit")
    people = len(ids(simulation, "person"))
    for variable in ("person_household_id", "person_benunit_id"):
        simulation.set_input(variable, 2025, np.zeros(people))

    simulation.subsample(n=5, seed=3)

    for entity, before in (("household", households), ("benunit", benunits)):
        assert members(simulation, entity) == {
            group: before[group] for group in ids(simulation, entity)
        }
    # Intended: the stored values are supplied inputs, so they are kept.
    assert set(values(simulation, "person_household_id", 2025).tolist()) == {0}


def test_zero_weight_households_are_never_kept():
    households = [(0.0, [1]), (50.0, [2]), (0.0, [1, 1]), (70.0, [1])]
    for seed in range(5):
        simulation = Microsimulation(dataset=dataset(households))
        simulation.subsample(n=6, seed=seed)
        assert set(ids(simulation, "household")) <= {
            FIRST_HOUSEHOLD_ID + 1,
            FIRST_HOUSEHOLD_ID + 3,
        }


# Weights.


def test_quantized_weights_count_draws_and_keep_every_years_total():
    simulation = Microsimulation(dataset=dataset())
    totals = {
        year: values(simulation, "household_weight", year).sum() for year in YEARS
    }

    simulation.subsample(n=7, seed=1, time_period=2027)

    draws = None
    for year in YEARS:
        weights = values(simulation, "household_weight", year)
        assert weights.sum() == pytest.approx(totals[year], rel=1e-5)
        multiples = weights * 7 / totals[year]
        assert np.abs(multiples - multiples.round()).max() < 1e-3
        assert multiples.round().sum() == 7
        # The same draws set the weights of every year.
        assert draws is None or multiples.round().tolist() == draws
        draws = multiples.round().tolist()


def test_unquantized_weights_scale_the_old_weights_by_draws():
    simulation = Microsimulation(dataset=dataset())
    before = weights_by_id(simulation, 2025)
    total = sum(before.values())

    simulation.subsample(n=5, seed=2, quantize_weights=False)

    after = weights_by_id(simulation, 2025)
    assert sum(after.values()) == pytest.approx(total, rel=1e-5)
    ratios = np.array([after[household] / before[household] for household in after])
    draws = ratios * 5 / ratios.sum()
    assert np.abs(draws - draws.round()).max() < 1e-3
    assert draws.round().sum() == 5


def test_other_supplied_weights_keep_their_totals_over_their_own_entity():
    data = dataset()
    data.household["original_weight"] = [7.0, 5.0, 3.0, 2.0, 1.0, 9.0]
    data.person["raw_person_weight"] = np.arange(1.0, len(data.person) + 1)
    simulation = Microsimulation(dataset=data)
    benunit_weight = values(simulation, "benunit_weight", 2025)
    simulation.set_input("benunit_weight", 2025, benunit_weight * 2)
    totals = {
        (name, year): values(simulation, name, year).sum()
        for name in ("original_weight", "raw_person_weight")
        for year in YEARS
    }
    totals["benunit_weight", 2025] = benunit_weight.sum() * 2

    simulation.subsample(n=4, seed=5)

    for (name, year), total in totals.items():
        assert values(simulation, name, year).sum() == pytest.approx(total, rel=1e-5)
        table = getattr(
            simulation.dataset[year],
            simulation.tax_benefit_system.get_variable(name).entity.key,
        )
        if name in table:
            assert table[name].sum() == pytest.approx(total, rel=1e-5)


def test_every_weight_variable_is_listed():
    """A new sampling weight must be rescaled by a subsample, so it has to be
    listed. A variable that only ends in "weight" must be left out on purpose:
    household_bus_fare_age_weight shares out bus fare spending by age."""
    named = {
        name for name in CountryTaxBenefitSystem().variables if name.endswith("weight")
    }
    assert named == WEIGHT_VARIABLES | {"household_bus_fare_age_weight"}


# Inputs.


def test_supplied_values_are_kept_and_calculated_values_are_not():
    simulation = Microsimulation(dataset=dataset())
    hours = np.arange(1.0, len(ids(simulation, "person")) + 1)
    simulation.set_input("hours_worked", 2027, hours)
    energy = np.arange(10.0, 10.0 + len(ids(simulation, "household")))
    simulation.set_input("monthly_domestic_energy_consumption", "2026-03", energy)
    hours_by_person = dict(zip(ids(simulation, "person"), hours))
    energy_by_household = dict(zip(ids(simulation, "household"), energy))
    ages = {year: by_id(simulation, "age", year) for year in YEARS}
    regions = by_id(simulation, "region", 2025)
    inputs = supplied(simulation)
    # Calculate results before subsampling; they must not become inputs.
    for variable in ("income_tax", "household_net_income", "universal_credit"):
        simulation.calculate(variable, 2026)
    simulation.calculate("age", 2035)
    income_tax = by_id(simulation, "income_tax", 2026)

    simulation.subsample(n=4, seed=4)

    assert supplied(simulation) == inputs
    for variable in ("income_tax", "household_net_income", "universal_credit"):
        assert simulation.get_holder(variable).get_known_periods() == []
    assert period_(2035) not in simulation.get_holder("age").get_known_periods()
    people = ids(simulation, "person")
    households = ids(simulation, "household")
    # A result calculated before is calculated again, on the sample.
    assert by_id(simulation, "income_tax", 2026) == {
        person: income_tax[person] for person in people
    }
    assert by_id(simulation, "hours_worked", 2027) == {
        person: hours_by_person[person] for person in people
    }
    assert by_id(simulation, "monthly_domestic_energy_consumption", "2026-03") == {
        household: energy_by_household[household] for household in households
    }
    for year in YEARS:
        assert by_id(simulation, "age", year) == {
            person: ages[year][person] for person in people
        }
    assert by_id(simulation, "region", 2025) == {
        household: regions[household] for household in households
    }


def test_a_calculated_value_that_replaced_an_input_is_not_kept():
    """The record of an input outlives a calculated value stored over it.
    The subsample must not keep the record: the next calculation would fill
    the period again, and the record would pass the result off as supplied."""
    simulation = Microsimulation(dataset=dataset())
    people = len(ids(simulation, "person"))
    simulation.set_input("hours_worked", 2027, np.full(people, 1_000.0))
    simulation.get_holder("hours_worked").put_in_cache(
        np.full(people, 500.0), period_(2027)
    )
    assert ("hours_worked", "2027") not in supplied(simulation)

    simulation.subsample(n=4, seed=4)
    simulation.calculate("hours_worked", 2027)

    assert ("hours_worked", "2027") not in supplied(simulation)
    assert "2027" not in simulation.to_input_dict().get("hours_worked", {})
    assert not any(
        name == "hours_worked" and str(period) == "2027"
        for name, _, period in simulation._user_input_keys
    )


def input_on_disk_under_a_cached_value(simulation, folder):
    """Store household_net_income for 2025 as an input on disk, then cache a
    calculated value over it in memory. Returns the input."""
    period = period_(2025)
    holder = simulation.get_holder("household_net_income")
    holder._disk_storage = OnDiskStorage(str(folder), preserve_storage_dir=True)
    holder._on_disk_storable = True
    # A memory limit no simulation can stay under sends the input to disk.
    simulation.memory_config = SimpleNamespace(max_memory_occupation_pc=-1)
    supplied_value = np.full(len(HOUSEHOLDS), 111.0)
    simulation.set_input("household_net_income", period, supplied_value)
    holder._on_disk_storable = False
    simulation.memory_config = None
    holder.put_in_cache(np.full(len(HOUSEHOLDS), 999.0), period)
    return supplied_value


def test_an_input_on_disk_is_kept_not_a_value_cached_over_it(tmp_path):
    simulation = Microsimulation(dataset=dataset())
    supplied_value = input_on_disk_under_a_cached_value(simulation, tmp_path)
    holder = simulation.get_holder("household_net_income")
    assert holder._memory_storage.get(period_(2025)).tolist() == [999.0] * 6

    assert stored_supplied_value(holder, period_(2025), "default").tolist() == (
        supplied_value.tolist()
    )
    simulation.subsample(n=2, seed=1)
    assert set(values(simulation, "household_net_income", 2025).tolist()) == {111.0}


def test_supplied_values_match_policyengine_cores_recorded_inputs(tmp_path):
    """Differential: policyengine-core 3.33 reads a recorded input from its
    tier in ``Simulation._get_recorded_input_array``; earlier versions have
    no such method, and ``stored_supplied_value`` follows the same rule."""
    simulation = Microsimulation(dataset=dataset())
    if not hasattr(simulation, "_get_recorded_input_array"):
        pytest.skip("policyengine-core reads recorded inputs from 3.33")
    input_on_disk_under_a_cached_value(simulation, tmp_path)
    people = len(ids(simulation, "person"))
    simulation.set_input("hours_worked", 2027, np.full(people, 1_000.0))
    simulation.get_holder("hours_worked").put_in_cache(
        np.full(people, 500.0), period_(2027)
    )
    simulation.calculate("income_tax", 2026)

    keys = sorted(simulation._user_input_keys, key=lambda key: (key[0], str(key[2])))
    assert keys
    for variable, branch, period in keys:
        ours = stored_supplied_value(simulation.get_holder(variable), period, branch)
        cores = simulation._get_recorded_input_array(variable, period)
        if cores is None:
            assert ours is None, (variable, period)
        else:
            assert np.asarray(ours).tolist() == np.asarray(cores).tolist(), (
                variable,
                period,
            )


def test_a_trace_starts_again_on_the_sample():
    simulation = Microsimulation(dataset=dataset(), trace=True)
    simulation.calculate("household_net_income", 2025)
    # A baseline traced in its simulation stays traced in it.
    simulation.baseline.tracer = simulation.tracer

    simulation.subsample(n=1, seed=1)
    simulation.calculate("household_net_income", 2025)

    assert isinstance(simulation.tracer, FullTracer)
    assert simulation.baseline.tracer is simulation.tracer
    flat = simulation.tracer.get_serialized_flat_trace()
    assert len(flat["household_net_income<2025, (default)>"]["value"]) == 1


def test_a_model_value_stays_the_models():
    """Formulas ask whether a value was supplied (``supplied_input``). A value
    the model stored as its own must not read as supplied after the rebuild,
    while a supplied one still does."""
    simulation = Microsimulation(dataset=dataset())
    benunits = ids(simulation, "benunit")
    model = np.arange(1.0, len(benunits) + 1) * 100
    set_model_value(simulation, "uc_LCWRA_element", 2026, model)
    simulation.set_input("uc_carer_element", 2026, np.full(len(benunits), 7.0))
    model_by_benunit = dict(zip(benunits, model))
    # The Universal Credit health element reform stores the model's own
    # values for other years in every simulation.
    model_periods = {
        str(period)
        for name, period, values in supplied_input_arrays(simulation)
        if is_model_value(simulation, name, period, values)
    }
    assert {"2026", "2027"} <= model_periods

    simulation.subsample(n=3, seed=1)

    benunit = simulation.populations["benunit"]
    kept = ids(simulation, "benunit")
    assert supplied_input(benunit, "uc_LCWRA_element", period_(2026)) is None
    assert by_id(simulation, "uc_LCWRA_element", 2026) == {
        unit: model_by_benunit[unit] for unit in kept
    }
    assert supplied_input(benunit, "uc_carer_element", period_(2026)).tolist() == (
        [7.0] * len(kept)
    )
    for held in (simulation, simulation.baseline):
        assert {
            str(period)
            for name, period, values in supplied_input_arrays(held)
            if is_model_value(held, name, period, values)
        } >= model_periods - {"2026"}


def test_where_capital_gains_inputs_came_from_is_kept():
    data = dataset()
    data.person["capital_gains"] = np.arange(len(data.person)) * 1_000.0
    simulation = Microsimulation(dataset=data)
    full = simulation.dataset
    before = simulation.capital_gains_projection_metadata["application"]
    statuses = {record["status"] for record in before["by_period"].values()}
    assert statuses == {"supplied", "projected"}

    simulation.subsample(n=3, seed=1)

    assert simulation.capital_gains_projection_metadata["application"] == before
    assert (
        simulation.dataset._cgt_extension_provenance == full._cgt_extension_provenance
    )
    # Differential: a simulation built from the subsampled dataset reports
    # the same origins as one built from the full dataset.
    rebuilt = Microsimulation(dataset=simulation.dataset)
    assert (
        rebuilt.capital_gains_projection_metadata["application"]
        == Microsimulation(dataset=full).capital_gains_projection_metadata[
            "application"
        ]
    )


def test_results_match_the_same_households_in_the_full_simulation():
    """Subsampling changes which households are held and their weights,
    not what the model calculates for a household."""
    full = Microsimulation(dataset=dataset())
    sample = Microsimulation(dataset=dataset())
    sample.subsample(n=4, seed=6, time_period=2026)

    for variable in ("income_tax", "household_net_income", "council_tax"):
        expected = by_id(full, variable, 2026)
        for record, value in by_id(sample, variable, 2026).items():
            assert value == pytest.approx(expected[record])


# Determinism.


def test_the_same_seed_keeps_the_same_households():
    samples = []
    for seed in (0, 0, "text seed", "text seed", None, None):
        simulation = Microsimulation(dataset=dataset())
        simulation.subsample(n=3, seed=seed, time_period=2026)
        samples.append(weights_by_id(simulation, 2026))

    assert samples[0] == samples[1]
    assert samples[2] == samples[3]
    assert samples[4] == samples[5]


def test_different_seeds_keep_different_households():
    weights = np.array([weight for weight, _ in HOUSEHOLDS])
    draws = {tuple(draw_household_counts(weights, 2, seed)) for seed in range(12)}
    assert len(draws) > 1


def test_frac_sets_the_number_of_draws():
    by_frac = Microsimulation(dataset=dataset())
    by_frac.subsample(frac=0.5, seed=8)
    by_n = Microsimulation(dataset=dataset())
    by_n.subsample(n=3, seed=8)

    assert weights_by_id(by_frac, 2025) == weights_by_id(by_n, 2025)


def test_a_period_before_the_data_samples_by_the_first_weights():
    """The model has no weights before the data's first year: it would give
    every household the default weight of one."""
    early = Microsimulation(dataset=dataset())
    assert set(values(early, "household_weight", 2020).tolist()) == {1.0}
    early.subsample(n=3, seed=9, time_period=2020)
    first = Microsimulation(dataset=dataset())
    first.subsample(n=3, seed=9, time_period=2025)

    assert weights_by_id(early, 2025) == weights_by_id(first, 2025)


# Baseline.


def test_a_reform_and_its_baseline_keep_the_same_households():
    reform = {PERSONAL_ALLOWANCE: 0}
    simulation = Microsimulation(dataset=dataset(), reform=reform)

    simulation.subsample(n=4, seed=0, time_period=2026)

    baseline = simulation.baseline
    assert 1 <= len(ids(simulation, "household")) <= 4
    for held in (baseline, baseline.baseline):
        assert ids(held, "household") == ids(simulation, "household")
        assert ids(held, "person") == ids(simulation, "person")
        assert weights_by_id(held, 2026) == weights_by_id(simulation, 2026)
    # Each simulation keeps its own policy, on the sample.
    sample = simulation.dataset
    reformed = Microsimulation(dataset=sample, reform=reform)
    unreformed = Microsimulation(dataset=sample)
    for held, expected in ((simulation, reformed), (baseline, unreformed)):
        assert values(held, "income_tax", 2026).tolist() == pytest.approx(
            values(expected, "income_tax", 2026).tolist()
        )
    assert (
        values(simulation, "income_tax", 2026).sum()
        > values(baseline, "income_tax", 2026).sum()
    )


@pytest.mark.parametrize("reform", [None, {PERSONAL_ALLOWANCE: 0}])
def test_subsampling_a_clone_leaves_the_source_and_its_baseline_alone(reform):
    """policyengine-core's ``clone`` shares a separate baseline between the
    source and the clone, so the clone must not subsample it in place."""
    source = Microsimulation(dataset=dataset(), reform=reform)
    baselines = []
    held = source
    while getattr(held, "baseline", None) is not None:
        held = held.baseline
        baselines.append((held, held.dataset, weights_by_id(held, 2026)))
    clone = source.clone()
    assert clone.baseline is source.baseline

    clone.subsample(n=2, seed=1)

    assert len(ids(clone, "household")) <= 2
    assert ids(clone.baseline, "household") == ids(clone, "household")
    assert len(ids(source, "household")) == len(HOUSEHOLDS)
    held = source
    for baseline, data, weights in baselines:
        assert held.baseline is baseline
        assert len(ids(baseline, "household")) == len(HOUSEHOLDS)
        assert baseline.dataset is data
        assert weights_by_id(baseline, 2026) == weights
        held = baseline
    # The source can still be subsampled on its own.
    source.subsample(n=3, seed=2)
    assert ids(source.baseline, "household") == ids(source, "household")


def test_the_baseline_held_before_is_left_as_it_was():
    simulation = Microsimulation(dataset=dataset())
    before = simulation.baseline

    simulation.subsample(n=2, seed=1)

    assert simulation.baseline is not before
    assert len(ids(before, "household")) == len(HOUSEHOLDS)
    assert ids(simulation.baseline, "household") == ids(simulation, "household")


def test_a_baseline_copy_does_not_copy_the_baselines_arrays(monkeypatch):
    """The copy of a baseline rebuilds its arrays at once, so copying the
    baseline's cached arrays first would only double its memory."""
    from policyengine_core.data_storage import InMemoryStorage

    from policyengine_uk.utils import subsample as module

    if module._branch_clone is None:
        pytest.skip("this policyengine-core cannot share a clone's arrays")
    simulation = Microsimulation(dataset=dataset(), reform={PERSONAL_ALLOWANCE: 0})
    simulation.baseline.calculate("household_net_income", 2026)
    calls = []
    clone = InMemoryStorage.clone

    def recording_clone(self, share_arrays=False):
        calls.append(share_arrays)
        return clone(self, share_arrays=share_arrays)

    monkeypatch.setattr(InMemoryStorage, "clone", recording_clone)

    simulation.subsample(n=3, seed=1)

    assert calls
    assert all(calls)


def test_a_baseline_holding_other_households_is_refused_and_nothing_changes():
    simulation = Microsimulation(dataset=dataset())
    simulation.baseline.subsample(n=2, seed=1)
    households = ids(simulation, "household")
    data = simulation.dataset

    with pytest.raises(ValueError, match="same households"):
        simulation.subsample(n=3, seed=0)

    assert ids(simulation, "household") == households
    assert simulation.dataset is data


# Dataset.


def test_the_dataset_holds_the_sample():
    simulation = Microsimulation(dataset=dataset())
    full = simulation.dataset
    full_households = len(full[2025].household)

    simulation.subsample(n=4, seed=0, time_period=2026)

    sample = simulation.dataset
    assert isinstance(sample, UKMultiYearDataset)
    assert sample is not full
    assert sample.years == full.years
    assert simulation.baseline.dataset is sample
    # The dataset the simulation was built from is not changed.
    assert len(full[2025].household) == full_households
    for year in sample.years:
        tables = sample[year]
        assert tables.household.household_id.tolist() == ids(simulation, "household")
        assert tables.benunit.benunit_id.tolist() == ids(simulation, "benunit")
        assert tables.person.person_id.tolist() == ids(simulation, "person")
        assert tables.household.household_weight.tolist() == pytest.approx(
            values(simulation, "household_weight", year).tolist(), rel=1e-5
        )
        assert tables.household.region.tolist() == list(
            values(simulation, "region", year)
        )


def test_inputs_set_after_the_build_stay_out_of_the_dataset():
    """Intended: ``dataset`` is the subsample of the dataset the simulation
    was built from, which held no values set afterwards either. So a later
    input stays in the simulation only, and a weight set on the simulation
    alone is rescaled to its own total there, while the baseline and the
    dataset keep the dataset's weights."""
    simulation = Microsimulation(dataset=dataset())
    people = len(ids(simulation, "person"))
    simulation.set_input("hours_worked", 2025, np.full(people, 1_234.0))
    simulation.set_input("household_weight", 2025, np.ones(len(HOUSEHOLDS)))
    hours_in_data = Microsimulation(dataset=simulation.dataset).calculate(
        "hours_worked", 2025
    )

    simulation.subsample(n=2, seed=1)

    rebuilt = Microsimulation(dataset=simulation.dataset)
    assert set(values(simulation, "hours_worked", 2025).tolist()) == {1_234.0}
    assert set(values(rebuilt, "hours_worked", 2025).tolist()) <= set(
        np.asarray(hours_in_data).tolist()
    )
    assert values(simulation, "household_weight", 2025).sum() == pytest.approx(
        len(HOUSEHOLDS)
    )
    total = sum(weight for weight, _ in HOUSEHOLDS)
    for held in (simulation.baseline, rebuilt):
        assert values(held, "household_weight", 2025).sum() == pytest.approx(total)


def test_an_input_for_part_of_a_year_stays_out_of_the_dataset():
    """Intended: a DataFrame can give a monthly input, which the simulation
    keeps and a dataset of whole years cannot hold, so a simulation built
    from the subsampled dataset does not have it."""
    frame = pd.DataFrame(
        {
            "person_id__2025": [1, 2],
            "household_id__2025": [1, 2],
            "household_weight__2025": [1.0, 1.0],
            "ebr_energy_bills_credit_eligible__2025-01": [False, False],
        }
    )
    simulation = Microsimulation(dataset=frame)

    simulation.subsample(n=1, seed=1)

    monthly = ("ebr_energy_bills_credit_eligible", "2025-01")
    assert monthly in supplied(simulation)
    assert values(simulation, *monthly).tolist() == [False]
    assert monthly not in supplied(Microsimulation(dataset=simulation.dataset))


def test_subsampling_a_single_year_dataset_keeps_its_type():
    data = dataset()
    counts = np.array([0, 2, 0, 1, 0, 0])
    household_ids = data.household.household_id.values

    sample = subsample_dataset(data, household_ids, counts)

    assert isinstance(sample, UKSingleYearDataset)
    assert sample.time_period == data.time_period
    assert sample.household.household_id.tolist() == household_ids[counts > 0].tolist()
    assert sample.household.household_weight.tolist() == pytest.approx([1_400.0, 700.0])
    assert len(data.household) == 6


def test_a_simulation_built_from_a_dataframe_subsamples_its_dataset():
    households = np.arange(4)
    frame = pd.DataFrame(
        {
            "person_id__2025": FIRST_PERSON_ID + households,
            "person_benunit_id__2025": FIRST_BENUNIT_ID + households,
            "person_household_id__2025": FIRST_HOUSEHOLD_ID + households,
            "benunit_id__2025": FIRST_BENUNIT_ID + households,
            "household_id__2025": FIRST_HOUSEHOLD_ID + households,
            "household_weight__2025": [10.0, 20.0, 30.0, 40.0],
            "age__2025": [30, 40, 50, 60],
        }
    )
    simulation = Microsimulation(dataset=frame)
    ages = by_id(simulation, "age", 2025)

    simulation.subsample(n=3, seed=1)

    kept = ids(simulation, "household")
    assert 1 <= len(kept) <= 3
    assert ids(simulation.baseline, "household") == kept
    assert sum(weights_by_id(simulation, 2025).values()) == pytest.approx(100.0)
    assert by_id(simulation, "age", 2025) == {
        person: ages[person] for person in ids(simulation, "person")
    }
    assert isinstance(simulation.dataset, UKMultiYearDataset)
    tables = simulation.dataset[2025]
    assert tables.household.household_id.tolist() == kept
    assert tables.household.household_weight.sum() == pytest.approx(100.0)


# Refusals.


def test_subsample_needs_n_or_frac():
    simulation = Microsimulation(dataset=dataset())
    with pytest.raises(ValueError, match="n or frac"):
        simulation.subsample(seed=0)


@pytest.mark.parametrize("n", [0, -3])
def test_subsample_needs_at_least_one_draw(n):
    simulation = Microsimulation(dataset=dataset())
    with pytest.raises(ValueError, match="at least one household"):
        simulation.subsample(n=n)
    assert len(ids(simulation, "household")) == len(HOUSEHOLDS)


def test_a_simulation_without_weights_is_refused():
    simulation = Microsimulation(dataset=dataset(weights=False))
    with pytest.raises(ValueError, match="household_weight"):
        simulation.subsample(n=2)


def test_a_negative_household_weight_is_refused_and_nothing_changes():
    simulation = Microsimulation(dataset=dataset([(1.0, [1]), (-2.0, [1])]))
    weights = weights_by_id(simulation, 2025)

    with pytest.raises(ValueError, match="negative"):
        simulation.subsample(n=1, seed=0)

    assert weights_by_id(simulation, 2025) == weights


def test_another_negative_weight_is_refused():
    data = dataset()
    data.household["original_weight"] = [1.0, 2.0, 3.0, -4.0, 5.0, 6.0]
    simulation = Microsimulation(dataset=data)
    households = ids(simulation, "household")

    with pytest.raises(ValueError, match="original_weight for 2025.*negative"):
        simulation.subsample(n=3)

    assert ids(simulation, "household") == households


def test_a_simulation_with_no_positive_weight_is_refused():
    households = [(0.0, [1]), (0.0, [2])]
    simulation = Microsimulation(dataset=dataset(households))
    with pytest.raises(ValueError, match="positive weight"):
        simulation.subsample(n=2)


def test_a_situation_is_refused():
    simulation = Simulation(situation={"age": 30})
    with pytest.raises(ValueError, match="built from a dataset"):
        simulation.subsample(n=1)


def test_a_branch_is_refused():
    simulation = Microsimulation(dataset=dataset())
    branch = simulation.get_branch("other")
    with pytest.raises(ValueError, match="branches"):
        branch.subsample(n=2)


def test_branches_are_made_again_on_the_sample():
    simulation = Microsimulation(dataset=dataset())
    simulation.get_branch("other").calculate("income_tax", 2026)

    simulation.subsample(n=3, seed=0)

    assert simulation.branches == {}
    branch = simulation.get_branch("other")
    assert ids(branch, "household") == ids(simulation, "household")
    assert len(branch.calculate("income_tax", 2026)) == len(ids(simulation, "person"))


def test_a_benefit_unit_across_households_is_refused():
    data = dataset()
    # Move the second person of the third household's first benefit unit to
    # the fourth household.
    data.person.loc[3, "person_household_id"] = FIRST_HOUSEHOLD_ID + 3
    simulation = Microsimulation(dataset=data)
    with pytest.raises(ValueError, match="more than one household"):
        simulation.subsample(n=3)


def test_a_total_that_cannot_be_kept_names_the_weight():
    simulation = Microsimulation(dataset=dataset())
    simulation.set_input("original_weight", 2026, [np.inf, 1.0, 1.0, 1.0, 1.0, 1.0])
    households = ids(simulation, "household")

    with pytest.raises(ValueError, match="original_weight for 2026.*finite total"):
        simulation.subsample(n=3)

    assert ids(simulation, "household") == households


@pytest.mark.parametrize("quantize", [True, False])
def test_a_weight_held_only_by_records_not_drawn_is_refused(quantize):
    """The third household holds all of the original weight and is never
    drawn, and the drawn ones stand for no one, so no sample keeps that
    total."""
    data = dataset([(100.0, [1]), (200.0, [2]), (0.0, [1])])
    data.household["original_weight"] = [0.0, 0.0, 9.0]
    simulation = Microsimulation(dataset=data)

    with pytest.raises(ValueError, match="original_weight for 2025.*no weight"):
        simulation.subsample(n=2, quantize_weights=quantize)


def test_a_zero_weight_stays_zero_in_every_year():
    """A household drawn by its positive weight in one year keeps a zero
    weight in a year where it has one, and the year's total goes to the
    drawn households that stand for someone that year."""
    years = []
    for year, weights in ((2025, [100.0, 200.0, 300.0]), (2026, [0.0, 200.0, 300.0])):
        years.append(dataset([(weight, [1]) for weight in weights], year=year))
    simulation = Microsimulation(dataset=UKMultiYearDataset(datasets=years))

    simulation.subsample(n=6, seed=0, time_period=2025)

    first = FIRST_HOUSEHOLD_ID
    kept = ids(simulation, "household")
    assert first in kept
    weights_2026 = weights_by_id(simulation, 2026)
    assert weights_2026[first] == 0
    assert sum(weights_2026.values()) == pytest.approx(500.0)
    assert sum(weights_by_id(simulation, 2025).values()) == pytest.approx(600.0)
    assert rescale_weights(np.array([0.0, 100, 100]), np.array([1, 1, 0])).tolist() == (
        [0.0, 200.0, 0.0]
    )


# Properties of the draw and the weights.

DRAW_SETTINGS = settings(max_examples=200, deadline=None, derandomize=True)
weight = st.one_of(
    st.just(0.0),
    st.floats(min_value=1e-3, max_value=1e6, allow_nan=False, allow_infinity=False),
)
weight_lists = st.lists(weight, min_size=1, max_size=40).filter(
    lambda weights: max(weights) > 0
)
seeds = st.one_of(st.integers(), st.text(max_size=8))


@DRAW_SETTINGS
@given(
    weights=weight_lists,
    n=st.integers(1, 60),
    seed=seeds,
    quantize=st.booleans(),
)
def test_draws_sum_to_n_and_skip_weightless_households(weights, n, seed, quantize):
    weights = np.array(weights)

    counts = draw_household_counts(weights, n, seed, quantize)

    assert counts.shape == weights.shape
    assert counts.sum() == n
    assert (counts >= 0).all()
    assert (counts[weights <= 0] == 0).all()
    assert 1 <= (counts > 0).sum() <= n
    assert counts.tolist() == draw_household_counts(weights, n, seed, quantize).tolist()


@DRAW_SETTINGS
@given(
    weights=weight_lists,
    n=st.integers(1, 60),
    seed=seeds,
    quantize=st.booleans(),
)
def test_rescaled_weights_keep_the_total(weights, n, seed, quantize):
    weights = np.array(weights)
    counts = draw_household_counts(weights, n, seed, quantize)

    rescaled = rescale_weights(weights, counts, quantize)

    assert rescaled.sum() == pytest.approx(weights.sum(), rel=1e-9)
    assert (rescaled[counts == 0] == 0).all()
    assert (rescaled[counts > 0] > 0).all()
    drawn = counts > 0
    shares = rescaled[drawn] / (
        counts[drawn] if quantize else weights[drawn] * counts[drawn]
    )
    assert shares == pytest.approx(np.full(drawn.sum(), shares[0]), rel=1e-9)


@DRAW_SETTINGS
@given(
    weights=weight_lists,
    counts=st.data(),
    quantize=st.booleans(),
)
def test_a_second_weight_keeps_its_own_total(weights, counts, quantize):
    """A weight is rescaled by draws made from another weight, as when a
    year's weights are rescaled by a sample drawn in another year."""
    weights = np.array(weights)
    counts = np.array(
        counts.draw(
            st.lists(st.integers(0, 5), min_size=len(weights), max_size=len(weights))
        )
    )
    drawn_weight = (counts * (weights > 0) if quantize else weights * counts).sum()
    if weights.sum() > 0 and drawn_weight == 0:
        with pytest.raises(ValueError, match="no weight"):
            rescale_weights(weights, counts, quantize)
        return

    rescaled = rescale_weights(weights, counts, quantize)

    assert rescaled.sum() == pytest.approx(weights.sum(), rel=1e-9)
    assert (rescaled[counts == 0] == 0).all()


def test_negative_sampling_weights_are_refused_before_drawing():
    """A negative weight would otherwise just never be drawn, and the total
    it lowers would be shared out among the drawn households."""
    with pytest.raises(ValueError, match="must not be negative to sample"):
        draw_household_counts(np.array([1.0, -2.0, 3.0]), 2, 0)


def test_weights_without_a_total_are_refused_or_stay_zero():
    counts = np.array([1, 2])
    assert rescale_weights(np.zeros(2), counts).tolist() == [0.0, 0.0]
    for weights in ([np.nan, 1.0], [np.inf, 1.0]):
        with pytest.raises(ValueError, match="finite total"):
            rescale_weights(np.array(weights), counts)
    with pytest.raises(ValueError, match="finite"):
        draw_household_counts(np.array([np.inf, 1.0]), 2, 0)


def mean_new_weights(weights, n, seeds, quantize):
    return np.mean(
        [
            rescale_weights(
                weights, draw_household_counts(weights, n, seed, quantize), quantize
            )
            for seed in range(seeds)
        ],
        axis=0,
    )


def test_a_households_mean_quantized_weight_is_its_old_weight():
    weights = np.array([1.0, 2.0, 3.0, 4.0, 0.0, 10.0, 30.0])

    mean = mean_new_weights(weights, n=40, seeds=3_000, quantize=True)

    assert mean == pytest.approx(weights, rel=0.03)


def test_unquantized_weights_are_a_ratio_estimate():
    """Intended: keeping the total exactly makes the unquantized weights a
    ratio estimate, so a household's mean new weight is off by a few per cent
    in a small sample and closes on its old weight as the sample grows."""
    weights = np.array([1.0, 2.0, 3.0, 4.0, 0.0, 10.0, 30.0])
    positive = weights > 0

    def error(n):
        mean = mean_new_weights(weights, n=n, seeds=1_500, quantize=False)
        return np.abs(mean[positive] / weights[positive] - 1).max()

    assert 0.04 < error(40) < 0.10
    assert error(400) < 0.02


def test_another_periods_mean_weight_follows_the_sampling_periods_shares():
    """Intended: households are drawn by their weights in the sampling period
    only, so in another period a household's mean new weight is its share of
    the sampling period's total times that period's total. That is its old
    weight there only if its share is the same in both periods."""
    sampling = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
    other = np.array([5.0, 1.0, 3.0, 4.0, 2.0])
    expected = sampling / sampling.sum() * other.sum()
    mean = np.mean(
        [
            rescale_weights(other, draw_household_counts(sampling, 40, seed))
            for seed in range(3_000)
        ],
        axis=0,
    )
    assert mean == pytest.approx(expected, rel=0.03)
    assert not np.allclose(mean, other, rtol=0.2)


# Properties of a subsampled simulation.

MAX_HOUSEHOLDS = 7
SIMULATION_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
household_specs = st.lists(
    st.tuples(
        st.one_of(st.just(0.0), st.floats(min_value=0.5, max_value=5_000.0)),
        st.lists(st.integers(1, 3), min_size=1, max_size=2),
    ),
    min_size=2,
    max_size=MAX_HOUSEHOLDS,
).filter(lambda households: any(weight > 0 for weight, _ in households))


MULTI_YEARS = (2025, 2026, 2027)


def multi_year_dataset(households, factors) -> UKMultiYearDataset:
    """A dataset of ``households`` for each of MULTI_YEARS, with each
    household's weight multiplied by its own factor in each year."""
    return UKMultiYearDataset(
        datasets=[
            dataset(
                [
                    (weight * factor, units)
                    for (weight, units), factor in zip(households, year_factors)
                ],
                year=year,
            )
            for year, year_factors in zip(MULTI_YEARS, factors)
        ]
    )


FACTORS = st.lists(
    st.lists(
        st.sampled_from([0.5, 0.8, 1.0, 1.25, 2.0]),
        min_size=MAX_HOUSEHOLDS,
        max_size=MAX_HOUSEHOLDS,
    ),
    min_size=len(MULTI_YEARS),
    max_size=len(MULTI_YEARS),
)
# Households whose shares of the total weight change from year to year.
CHANGING_SHARES = dict(
    households=[(100.0, [1]), (300.0, [2]), (0.0, [1]), (50.0, [1, 2])],
    n=6,
    seed=11,
    multi_year=True,
    factors=[[1.0] * MAX_HOUSEHOLDS, [2.0, 0.5, 1.0, 1.25, 1, 1, 1], [0.5] + [2.0] * 6],
    year_index=1,
)


@SIMULATION_SETTINGS
@given(
    households=household_specs,
    n=st.integers(1, 10),
    seed=st.integers(0, 10_000),
    quantize=st.booleans(),
    multi_year=st.booleans(),
    factors=FACTORS,
    year_index=st.integers(0, len(YEARS) - 1),
)
@example(quantize=True, **CHANGING_SHARES)
@example(quantize=False, **CHANGING_SHARES)
def test_subsample_properties(
    households, n, seed, quantize, multi_year, factors, year_index
):
    if multi_year:
        factors = [year_factors[: len(households)] for year_factors in factors]
        years = list(MULTI_YEARS)
    else:
        years = list(YEARS)
    year = years[year_index % len(years)]

    def build():
        if multi_year:
            return Microsimulation(dataset=multi_year_dataset(households, factors))
        return Microsimulation(dataset=dataset(households))

    def subsample():
        return build().subsample(
            n=n, seed=seed, time_period=year, quantize_weights=quantize
        )

    full = build()
    sample = subsample()
    kept = ids(sample, "household")
    people = ids(sample, "person")

    # 1. Size.
    assert 1 <= len(kept) <= n
    full_weights = {period: weights_by_id(full, period) for period in years}
    assert all(full_weights[year][household] > 0 for household in kept)

    draws_by_period = {}
    for period in years:
        weights = weights_by_id(sample, period)
        total = sum(full_weights[period].values())
        # 2. Weight totals.
        assert sum(weights.values()) == pytest.approx(total, rel=1e-5)
        # 3. Quantized weights: whole numbers of draws, of the old weight
        # when the weights are not quantized.
        shares = np.array(
            [
                weights[household]
                / (1 if quantize else full_weights[period][household])
                for household in kept
            ]
        )
        draws = shares * n / shares.sum()
        assert np.abs(draws - draws.round()).max() < 1e-2
        assert draws.round().sum() == n
        draws_by_period[period] = draws.round().tolist()
    # The same draws set the weights of every period.
    assert len({tuple(draws) for draws in draws_by_period.values()}) == 1

    # 4. Links.
    for entity in ("household", "benunit"):
        full_members = members(full, entity)
        sample_members = members(sample, entity)
        assert all(sample_members.values())
        assert sample_members == {
            group: full_members[group] for group in sample_members
        }
    assert set(people) == set().union(*members(sample, "household").values())
    assert set(people) == set().union(*members(sample, "benunit").values())
    assert len(set(people)) == len(people)

    # 5. Inputs.
    assert supplied(sample) == supplied(full)
    for period in years:
        for variable in ("age", "employment_income", "region", "council_tax"):
            expected = by_id(full, variable, period)
            assert by_id(sample, variable, period) == {
                record: expected[record]
                for record in ids(
                    sample, sample.tax_benefit_system.get_variable(variable).entity.key
                )
            }

    # 6. Determinism.
    again = subsample()
    assert ids(again, "person") == people
    for period in years:
        assert weights_by_id(again, period) == weights_by_id(sample, period)

    # 7. Baseline.
    assert ids(sample.baseline, "household") == kept
    assert ids(sample.baseline, "person") == people
    assert weights_by_id(sample.baseline, year) == weights_by_id(sample, year)

    # 8. Dataset, and a simulation built from it.
    rebuilt = Microsimulation(dataset=sample.dataset)
    for entity in ("person", "benunit", "household"):
        assert ids(rebuilt, entity) == ids(sample, entity)
        assert getattr(sample.dataset[year], entity)[f"{entity}_id"].tolist() == ids(
            sample, entity
        )
    for period in years:
        assert list(weights_by_id(rebuilt, period).values()) == pytest.approx(
            list(weights_by_id(sample, period).values()), rel=1e-5
        )
    for variable in ("household_net_income", "income_tax", "universal_credit"):
        assert values(rebuilt, variable, year).tolist() == pytest.approx(
            values(sample, variable, year).tolist()
        )
