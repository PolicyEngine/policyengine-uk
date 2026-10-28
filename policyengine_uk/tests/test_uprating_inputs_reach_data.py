"""Parameter changes that reach the dataset uprating reach the data.

A single-year dataset is extended to later years and uprated from the
parameters as they stand when the data is built
(``policyengine_uk.data.economic_assumptions``). ``hf://`` and ``gs://``
datasets are cached once extended.

Invariants:

1. Cache isolation: the cached dataset is uprated under current law. A
   simulation whose uprating inputs differ (a macro scenario,
   ``no_economic_assumptions``) neither reads nor writes it, so it gets its
   own projection and every other simulation, its own baseline included,
   gets current law's, in either order.
2. Current-law simulations still share one extension, ordinary reforms
   included.
3. Data follows the parameters: a reform dict that changes a growth rate the
   uprating reads projects the data by that rate in that year and by current
   law's in every other year, exactly as the scenario applied before the data
   load does; an ordinary reform leaves the data as current law's.
4. Fingerprint: equal for equal uprating inputs, different when any read
   input changes, and covering every parameter the uprating reads (checked
   by recording the reads).

All datasets here are MOCK data: two synthetic households, not survey
records.
"""

import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import Parameter, ParameterNode

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data import economic_assumptions
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    uprating_input_fingerprint,
    uprating_input_paths,
)
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.tax_benefit_system import CountryTaxBenefitSystem
from policyengine_uk.utils.scenario import Scenario

AVERAGE_EARNINGS = "gov.economic_assumptions.yoy_growth.obr.average_earnings"
# The index employee_pension_contributions_reported declares. The YAML does
# not list that variable, so only the post-2030 fallback reads its index.
UNMAPPED_INDEX = "gov.economic_assumptions.indices.obr.average_earnings"
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
HF_URL = "hf://policyengine/policyengine-uk-data-private/mock_frs_2025_26.h5"
GCS_URL = "gs://policyengine-uk-data-private/mock_frs_2025_26.h5"
CURRENT_LAW_2027 = 0.024  # yoy_growth.obr.average_earnings for 2027

PROPERTY_SETTINGS = settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)


def mock_dataset() -> UKSingleYearDataset:
    """MOCK data: two synthetic households with the columns uprating reads."""
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 2],
            "person_household_id": [1, 2],
            "age": [40, 70],
            "employment_income": [30_000.0, 0.0],
        }
    )
    benunit = pd.DataFrame({"benunit_id": [1, 2]})
    household = pd.DataFrame(
        {
            "household_id": [1, 2],
            "household_weight": [1.0, 1.0],
            "region": ["LONDON", "WALES"],
            "tenure_type": ["RENT_PRIVATELY", "OWNED_OUTRIGHT"],
            "rent": [12_000.0, 0.0],
            "council_tax": [1_500.0, 1_800.0],
        }
    )
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=2025
    )


def mock_dataset_with_every_uprated_input() -> UKSingleYearDataset:
    """MOCK data carrying every variable the extension uprates.

    The indices of the variables ``uprating_indices.yaml`` leaves out are
    read only for the variables a dataset has, so the read-set check needs
    them all.
    """
    from policyengine_uk.system import system

    dataset = mock_dataset()
    tables = {
        "person": dataset.person,
        "benunit": dataset.benunit,
        "household": dataset.household,
    }
    uprating = economic_assumptions._uprating_index_map()
    names = set(economic_assumptions._unmapped_uprating_indices(uprating))
    names |= {name for variables in uprating.values() for name in variables}
    # Uprated by country rather than through the index map (#2501).
    names |= economic_assumptions.COUNTRY_UPRATED_INPUTS
    for name in sorted(names):
        variable = system.variables.get(name)
        if variable is None or variable.value_type is not float:
            continue
        table = tables[variable.entity.key]
        if name not in table.columns:
            table[name] = 1.0
    return UKSingleYearDataset(**tables, fiscal_year=2025)


@pytest.fixture(scope="module")
def mock_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("mock") / "mock_frs_2025_26.h5"
    mock_dataset().save(str(path))
    return str(path)


@pytest.fixture
def remote(monkeypatch, mock_path):
    """Serve both URL schemes from the MOCK file, with an empty cache, and
    count extensions."""
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    monkeypatch.setattr(
        simulation_module, "download_huggingface_dataset", lambda **_: mock_path
    )
    monkeypatch.setattr(
        simulation_module, "materialize_gcs_dataset_url", lambda url: mock_path
    )
    calls = []

    def counting_extend(dataset, parameters, *args, **kwargs):
        calls.append(dataset.time_period)
        return extend_single_year_dataset(dataset, parameters, *args, **kwargs)

    monkeypatch.setattr(
        simulation_module, "extend_single_year_dataset", counting_extend
    )
    return calls


def growth(simulation, year=2027):
    """Employment income growth into ``year`` in the simulation's data."""
    data = simulation.dataset
    return (
        data[year].person["employment_income"].sum()
        / data[year - 1].person["employment_income"].sum()
        - 1
    )


def macro(rate=0.2, year=2027):
    return Scenario(
        parameter_changes={AVERAGE_EARNINGS: {f"year:{year}-01-01:1": rate}},
        applied_before_data_load=True,
    )


# 1. Cache isolation.


@pytest.mark.parametrize("url", [HF_URL, GCS_URL], ids=["hf", "gs"])
@pytest.mark.parametrize(
    "macro_first", [True, False], ids=["macro-first", "baseline-first"]
)
def test_a_macro_scenario_and_current_law_get_their_own_data(remote, url, macro_first):
    if macro_first:
        reformed = Simulation(dataset=url, scenario=macro())
        later = Simulation(dataset=url)
    else:
        later = Simulation(dataset=url)
        reformed = Simulation(dataset=url, scenario=macro())
    assert growth(reformed) == pytest.approx(0.2)
    assert growth(reformed.baseline) == pytest.approx(CURRENT_LAW_2027)
    assert growth(later) == pytest.approx(CURRENT_LAW_2027)
    # Only current law's projection is cached.
    assert list(simulation_module._url_dataset_cache) == [url]


@pytest.mark.parametrize("no_assumptions_first", [True, False])
def test_no_economic_assumptions_does_not_reach_later_simulations(
    remote, no_assumptions_first
):
    if no_assumptions_first:
        frozen = Simulation(dataset=HF_URL, scenario=no_economic_assumptions)
        later = Simulation(dataset=HF_URL)
    else:
        later = Simulation(dataset=HF_URL)
        frozen = Simulation(dataset=HF_URL, scenario=no_economic_assumptions)
    assert growth(frozen) == 0
    assert growth(later) == pytest.approx(CURRENT_LAW_2027)


# 2. Current-law simulations share one extension.


def test_current_law_and_ordinary_reforms_share_one_extension(remote):
    first = Simulation(dataset=HF_URL)
    second = Simulation(dataset=HF_URL)
    reformed = Simulation(dataset=HF_URL, reform={PERSONAL_ALLOWANCE: 20_000})
    assert len(remote) == 1
    assert second.dataset is first.dataset
    assert reformed.dataset is first.dataset
    assert reformed.baseline.dataset is first.dataset


# 3. Data follows the parameters.


def all_years(simulation, column="employment_income"):
    data = simulation.dataset
    return {year: list(data[year].person[column]) for year in data.years}


def test_a_growth_reform_dict_projects_the_data_as_the_before_load_route(mock_path):
    change = {AVERAGE_EARNINGS: {"year:2027-01-01:1": 0.2}}
    by_dict = Simulation(dataset=mock_path, reform=change)
    before_load = Simulation(
        dataset=mock_path,
        scenario=Scenario(parameter_changes=change, applied_before_data_load=True),
    )
    assert growth(by_dict) == pytest.approx(0.2)
    assert all_years(by_dict) == all_years(before_load)
    calculated = (
        by_dict.calculate("employment_income", 2027).sum()
        / by_dict.calculate("employment_income", 2026).sum()
    )
    assert calculated == pytest.approx(1.2)
    assert growth(by_dict.baseline) == pytest.approx(CURRENT_LAW_2027)


def test_a_macro_scenario_combined_with_a_reform_still_projects_the_data(mock_path):
    # Scenario.__add__ makes the sum an after-load scenario.
    combined = macro() + Scenario.from_reform({PERSONAL_ALLOWANCE: 20_000})
    simulation = Simulation(dataset=mock_path, scenario=combined)
    assert growth(simulation) == pytest.approx(0.2)
    assert (
        simulation.tax_benefit_system.parameters.get_child(PERSONAL_ALLOWANCE)(
            "2027-01-01"
        )
        == 20_000
    )


def test_an_ordinary_reform_keeps_the_data_and_the_after_build_timing(
    mock_path, monkeypatch
):
    events = []
    build = Simulation.build_from_dataset_source
    apply = Simulation.apply_scenario_parameters

    def recording_build(self, source):
        events.append("build")
        return build(self, source)

    def recording_apply(self, scenario):
        events.append("parameters")
        return apply(self, scenario)

    monkeypatch.setattr(Simulation, "build_from_dataset_source", recording_build)
    monkeypatch.setattr(Simulation, "apply_scenario_parameters", recording_apply)
    reformed = Simulation(dataset=mock_path, reform={PERSONAL_ALLOWANCE: 20_000})
    # The reform's own build, then its parameters, then its baseline's build.
    assert events == ["build", "parameters", "build"]
    assert all_years(reformed) == all_years(reformed.baseline)


@pytest.mark.parametrize("source", ["situation", "dataframe"])
def test_sources_that_are_not_projected_skip_the_uprating_check(
    mock_path, monkeypatch, source
):
    checks = []
    monkeypatch.setattr(
        Simulation,
        "_scenario_changes_uprating_inputs",
        lambda self, scenario: checks.append(scenario) or True,
    )
    change = {AVERAGE_EARNINGS: {"year:2027-01-01:1": 0.2}}
    if source == "situation":
        situation = {
            "people": {
                "adult": {"age": {2025: 40}, "employment_income": {2025: 30_000}}
            },
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {"household": {"members": ["adult"]}},
        }
        reformed = Simulation(situation=situation, reform=change)
    else:
        frame = Simulation(dataset=mock_path).to_input_dataframe()
        reformed = Simulation(dataset=frame, reform=change)
    assert checks == []
    # The reform still reaches the parameters.
    assert reformed.tax_benefit_system.parameters.get_child(AVERAGE_EARNINGS)(
        "2027-01-01"
    ) == pytest.approx(0.2)


@PROPERTY_SETTINGS
@given(
    rate=st.integers(-50, 300).map(lambda n: n / 1000),
    year=st.integers(2026, 2030),
)
def test_a_growth_reform_moves_the_data_in_its_year_only(mock_path, rate, year):
    reformed = Simulation(
        dataset=mock_path,
        reform={AVERAGE_EARNINGS: {f"year:{year}-01-01:1": rate}},
    )
    for later in range(2026, 2033):
        expected = rate if later == year else growth(reformed.baseline, later)
        assert growth(reformed, later) == pytest.approx(expected, abs=1e-9)


# 4. Fingerprint.


def current_law_parameters():
    """A copy of current law's processed parameters, CGT projection index
    included. Copied from the module's system: building a system while the
    tests are collected would leave its variable modules frozen
    (``test_variable_module_release``)."""
    from policyengine_uk.tax_benefit_system import system

    return system.parameters.clone()


def read_leaves():
    from policyengine_uk.tax_benefit_system import system

    parameters = system.parameters
    leaves = []
    for path in uprating_input_paths():
        node = parameters.get_child(path)
        if isinstance(node, Parameter):
            leaves.append(path)
        else:
            leaves += [
                p.name for p in node.get_descendants() if isinstance(p, Parameter)
            ]
    return sorted(leaves)


READ_LEAVES = read_leaves()


@settings(max_examples=40, deadline=None, derandomize=True)
@given(
    leaf=st.sampled_from(READ_LEAVES),
    entry=st.integers(0, 10_000),
    delta=st.sampled_from([1e-6, 0.01, -0.5]),
)
def test_the_fingerprint_changes_with_any_read_input(leaf, entry, delta):
    current = uprating_input_fingerprint(current_law_parameters())
    parameters = current_law_parameters()
    assert uprating_input_fingerprint(parameters) == current
    parameter = parameters.get_child(leaf)
    values = parameter.values_list
    target = values[entry % len(values)]
    target.value = (target.value or 0) + delta
    assert uprating_input_fingerprint(parameters) != current


def test_the_fingerprint_covers_every_parameter_the_uprating_reads(monkeypatch):
    read = set()
    get_child = ParameterNode.get_child
    parameter_at = Parameter._get_at_instant
    node_at = ParameterNode._get_at_instant

    def recording_get_child(self, path):
        read.add(f"{self.name}.{path}" if self.name else path)
        return get_child(self, path)

    def recording_parameter_at(self, instant):
        read.add(self.name)
        return parameter_at(self, instant)

    def recording_node_at(self, instant):
        read.add(self.name)
        return node_at(self, instant)

    parameters = current_law_parameters()
    monkeypatch.setattr(ParameterNode, "get_child", recording_get_child)
    monkeypatch.setattr(Parameter, "_get_at_instant", recording_parameter_at)
    monkeypatch.setattr(ParameterNode, "_get_at_instant", recording_node_at)
    # Past the legacy horizon, so the unmapped indices are read too.
    extend_single_year_dataset(mock_dataset_with_every_uprated_input(), parameters)
    monkeypatch.undo()

    covered = uprating_input_paths()
    # The unmapped indices, read past the legacy horizon, are in the set.
    assert UNMAPPED_INDEX in read
    for name in read:
        assert any(name == path or name.startswith(f"{path}.") for path in covered), (
            name
        )


def test_the_read_set_names_inputs_outside_the_growth_rates():
    paths = uprating_input_paths()
    assert UNMAPPED_INDEX in paths
    assert economic_assumptions.CGT_INDEX_PATH in paths
    assert AVERAGE_EARNINGS in paths


def test_the_probe_leaves_the_system_as_it_was():
    from policyengine_uk.utils.scenario import Scenario as S

    simulation = Simulation.__new__(Simulation)
    simulation.tax_benefit_system = CountryTaxBenefitSystem()
    system = simulation.tax_benefit_system
    before = uprating_input_fingerprint(system.parameters)
    parameters = system.parameters
    change = S(parameter_changes={AVERAGE_EARNINGS: {"year:2027-01-01:1": 0.2}})
    assert simulation._scenario_changes_uprating_inputs(change)
    assert system.parameters is parameters
    assert system.dated_assignments == []
    assert uprating_input_fingerprint(system.parameters) == before
    ordinary = S(parameter_changes={PERSONAL_ALLOWANCE: 20_000})
    assert not simulation._scenario_changes_uprating_inputs(ordinary)


def test_a_failing_probe_leaves_the_system_and_its_caches_alone():
    from policyengine_uk.utils.dated_reforms import ParameterAssignment
    from policyengine_core.periods import instant

    system = CountryTaxBenefitSystem()
    parameters = system.parameters
    # Fill some node caches.
    parameters("2027-01-01")
    filled = [
        n for n in parameters.get_descendants() if getattr(n, "_at_instant_cache", None)
    ]
    assert filled
    bad = ParameterAssignment(
        "gov.not.a.parameter", instant("2027-01-01"), instant("2027-12-31"), 1
    )
    with pytest.raises(ValueError, match="Could not find the parameter"):
        system.parameters_with([bad])
    assert system.parameters is parameters
    assert all(getattr(n, "_at_instant_cache", None) for n in filled)
    # With no changes, the tree returned is a copy, not the system's own.
    assert system.parameters_with([]) is not system.parameters
