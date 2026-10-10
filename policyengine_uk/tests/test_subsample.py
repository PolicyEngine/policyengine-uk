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
   weight is a whole multiple of total / ``n``, and the multiples sum to ``n``.
   Without it, a household's weight is proportional to its old weight times a
   whole number of draws.
4. Links: a kept household or benefit unit has exactly the people it had, a
   kept person keeps their household and benefit unit, and no other record is
   kept. This holds for identifiers that 32-bit floats cannot tell apart.
5. Inputs: every supplied value other than a weight is unchanged for the kept
   records, in every period, and the subsample supplies the same variables
   and periods as before. Calculated values are not kept.
6. Determinism: the same seed keeps the same households with the same weights.
7. Baseline: the baseline holds the same households and weights, and each
   simulation keeps its own policy.
8. Dataset (differential): ``dataset`` holds the same records and weights as
   the populations, and a simulation built from it gives the same results as
   the subsampled simulation.
9. Unbiasedness: over many seeds, a household's mean quantized weight is its
   old weight. Intended exception: unquantized weights keep the total exactly
   and are therefore a ratio estimate, whose mean is off by a few per cent in
   a small sample and closes on the old weight as the sample grows.

Intended exceptions: a simulation built from a situation, one given no
household weights, a branch, and a baseline holding other households raise
``ValueError`` and are left unchanged.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import period as period_

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.utils.subsample import (
    WEIGHT_VARIABLES,
    draw_household_counts,
    rescale_weights,
    subsample_dataset,
)
from policyengine_uk.utils.supplied_inputs import supplied_input_arrays

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = range(2025, 2031)
# Neighbouring identifiers of the size the UK datasets use. As 32-bit floats,
# which is how the model stores person_household_id and person_benunit_id,
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
    # The stored membership inputs cannot tell these households apart.
    stored = values(simulation, "person_household_id", 2025)
    assert len(set(stored.tolist())) < len(households)

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

    simulation.subsample(n=4, seed=4)

    assert supplied(simulation) == inputs
    for variable in ("income_tax", "household_net_income", "universal_credit"):
        assert simulation.get_holder(variable).get_known_periods() == []
    assert period_(2035) not in simulation.get_holder("age").get_known_periods()
    people = ids(simulation, "person")
    households = ids(simulation, "household")
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


def test_unquantized_weights_need_a_sampled_record_with_weight():
    """The third household holds all of the original weight and is never
    drawn, so scaling the old weights cannot keep that total; counting draws
    can."""
    data = dataset([(100.0, [1]), (200.0, [2]), (0.0, [1])])
    data.household["original_weight"] = [0.0, 0.0, 9.0]
    simulation = Microsimulation(dataset=data)

    with pytest.raises(ValueError, match="original_weight for 2025.*no weight"):
        simulation.subsample(n=2, quantize_weights=False)

    simulation.subsample(n=2)
    assert values(simulation, "original_weight", 2025).sum() == pytest.approx(9.0)


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
    drawn_weight = (counts if quantize else weights * counts).sum()
    if weights.sum() > 0 and drawn_weight == 0:
        with pytest.raises(ValueError, match="no weight"):
            rescale_weights(weights, counts, quantize)
        return

    rescaled = rescale_weights(weights, counts, quantize)

    assert rescaled.sum() == pytest.approx(weights.sum(), rel=1e-9)
    assert (rescaled[counts == 0] == 0).all()


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


# Properties of a subsampled simulation.

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
    max_size=7,
).filter(lambda households: any(weight > 0 for weight, _ in households))


@SIMULATION_SETTINGS
@given(
    households=household_specs,
    n=st.integers(1, 10),
    seed=st.integers(0, 10_000),
    year=st.sampled_from(list(YEARS)),
    quantize=st.booleans(),
)
def test_subsample_properties(households, n, seed, year, quantize):
    def subsample():
        simulation = Microsimulation(dataset=dataset(households))
        return simulation.subsample(
            n=n, seed=seed, time_period=year, quantize_weights=quantize
        )

    full = Microsimulation(dataset=dataset(households))
    sample = subsample()
    kept = ids(sample, "household")
    people = ids(sample, "person")

    # 1. Size.
    assert 1 <= len(kept) <= n
    full_weights = {period: weights_by_id(full, period) for period in YEARS}
    assert all(full_weights[year][household] > 0 for household in kept)

    for period in YEARS:
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
    for period in YEARS:
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
    for period in YEARS:
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
    for period in YEARS:
        assert list(weights_by_id(rebuilt, period).values()) == pytest.approx(
            list(weights_by_id(sample, period).values()), rel=1e-5
        )
    for variable in ("household_net_income", "income_tax", "universal_credit"):
        assert values(rebuilt, variable, year).tolist() == pytest.approx(
            values(sample, variable, year).tolist()
        )
