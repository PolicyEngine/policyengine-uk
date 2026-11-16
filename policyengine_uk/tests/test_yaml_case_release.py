"""The conftest releases each YAML case's simulation and reformed systems.

policyengine-core's YAML runner keeps every case's simulation, and every
system it built for dotted parameter inputs, until the process ends. The
conftest's ``release_yaml_case`` drops a case's simulation and system after
it runs, and a file's dotted-input systems after its last case, so the YAML
run's peak memory falls from 16.1 GiB to 1.65 GiB. If core starts releasing
them itself (PolicyEngine/policyengine-core#569), the first test skips with
a note to remove the workaround. If core keeps the cache but changes its
keys, the last test fails, because the release would then silently do
nothing.
"""

from contextlib import contextmanager
from pathlib import Path

import pytest
from policyengine_core.tools import test_runner
from policyengine_core.tools.test_runner import YamlItem

PLAIN = ("", "", frozenset())
NAMED = ("policyengine_uk.reforms.example", "", frozenset())
DOTTED = ("", "gov.x:1", frozenset())
NAMED_AND_DOTTED = ("policyengine_uk.reforms.example", "gov.x:1", frozenset())


def _conftest(request):
    path = Path(__file__).with_name("conftest.py")
    for plugin in request.config.pluginmanager.get_plugins():
        if getattr(plugin, "__file__", None) and Path(plugin.__file__) == path:
            return plugin
    raise AssertionError(f"{path} is not loaded as a plugin")


class _Baseline:
    """A stand-in baseline system, which the cache holds weakly."""

    def clone(self):
        return _Baseline()


@contextmanager
def _cached(keys):
    """Cache a system under each key for a stand-in baseline, then remove it."""
    baseline = _Baseline()
    test_runner._tax_benefit_system_cache[baseline] = {key: object() for key in keys}
    try:
        yield test_runner._tax_benefit_system_cache[baseline]
    finally:
        test_runner._tax_benefit_system_cache.pop(baseline, None)


def _case(path: str) -> YamlItem:
    # A case as the runner leaves it once it has run.
    case = object.__new__(YamlItem)
    case.path = Path(path)
    case.simulation = object()
    case.tax_benefit_system = object()
    return case


def test_core_still_keeps_yaml_cases():
    if "teardown" in vars(YamlItem):
        pytest.skip(
            "policyengine-core's YamlItem now has its own teardown "
            "(PolicyEngine/policyengine-core#569). If it releases each case's "
            "simulation and bounds _tax_benefit_system_cache, remove "
            "release_yaml_case from conftest.py, and this file."
        )


def test_a_case_releases_its_simulation_and_system(request):
    release_yaml_case = _conftest(request).release_yaml_case
    case = _case("a.yaml")
    release_yaml_case(case, _case("a.yaml"))
    assert case.simulation is None
    assert case.tax_benefit_system is None


def test_a_files_last_case_drops_only_its_dotted_input_systems(request):
    release_yaml_case = _conftest(request).release_yaml_case
    with _cached([PLAIN, NAMED, DOTTED, NAMED_AND_DOTTED]) as systems:
        # Later cases in the same file may reuse the file's systems.
        release_yaml_case(_case("a.yaml"), _case("a.yaml"))
        assert set(systems) == {PLAIN, NAMED, DOTTED, NAMED_AND_DOTTED}
        release_yaml_case(_case("a.yaml"), _case("b.yaml"))
        assert set(systems) == {PLAIN, NAMED}
    with _cached([PLAIN, DOTTED]) as systems:
        release_yaml_case(_case("a.yaml"), None)
        assert set(systems) == {PLAIN}


def test_other_tests_release_nothing(request):
    release_yaml_case = _conftest(request).release_yaml_case
    with _cached([PLAIN, DOTTED]) as systems:
        release_yaml_case(request.node, None)
        assert set(systems) == {PLAIN, DOTTED}


def test_the_cache_keys_hold_the_dotted_inputs_second():
    # release_yaml_case reads a key's second part as its dotted inputs.
    with _cached([]) as systems:
        (baseline,) = [
            key
            for key, value in test_runner._tax_benefit_system_cache.items()
            if value is systems
        ]
        test_runner._get_tax_benefit_system(baseline, [], [], reform_key="gov.x:1")
        assert set(systems) == {DOTTED}
