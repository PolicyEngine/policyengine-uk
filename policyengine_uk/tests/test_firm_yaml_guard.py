"""Guard: YAML policy tests never give firms through a ``firms:`` block.

The YAML test runner builds each case with policyengine-core's
``SimulationBuilder.build_from_dict``, which knows only people and their
groups. Observed behaviour (policyengine-core 3.34.9):

- With people in the situation, a ``firms:`` block is silently ignored: the
  simulation has no firms, a firm variable comes back as an empty array, and
  core's ``assert_near`` passes an empty array against any expected value. A
  firm test written that way passes whatever it expects.
- With a ``firms:`` block alone, the builder raises a ``SituationParsingError``
  ("No person found").

Firm YAML tests must therefore give firm variables directly (variable-only
input, one array position per firm). Mixed household and firm cases belong in
Python tests, where the UK ``Simulation`` reads a situation's ``firms`` entry.
"""

from pathlib import Path

import numpy as np
import pytest
import yaml
from policyengine_core.errors import SituationParsingError
from policyengine_core.simulations import SimulationBuilder
from policyengine_core.tools import assert_near

from policyengine_uk import CountryTaxBenefitSystem

POLICY_TESTS = Path(__file__).parent / "policy"
YEAR = 2026
FIRMS = {"acme": {"firm_paybill": 1_000_000}}


def _cases(path: Path):
    tests = yaml.safe_load(path.read_text())
    for case in tests if isinstance(tests, list) else [tests]:
        if isinstance(case, dict):
            yield case


def firms_block_cases(root: Path) -> list:
    """Every YAML test case under ``root`` whose input has a ``firms`` key."""
    paths = sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.yml"))
    return [
        f"{path.relative_to(root)}: {case.get('name', '<unnamed>')}"
        for path in paths
        for case in _cases(path)
        if isinstance(case.get("input"), dict) and "firms" in case["input"]
    ]


def test_no_yaml_policy_test_has_a_firms_block():
    assert any(POLICY_TESTS.rglob("*.yaml")), "No YAML policy tests found"
    offenders = firms_block_cases(POLICY_TESTS)
    assert not offenders, (
        "YAML tests must not use a `firms:` block (the core builder ignores "
        "it); give firm variables directly instead:\n" + "\n".join(offenders)
    )


def test_the_guard_finds_a_firms_block(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "cases.yaml").write_text(
        yaml.safe_dump(
            [
                {
                    "name": "Case 1, firms block.",
                    "period": YEAR,
                    "input": {"people": {"person1": {}}, "firms": FIRMS},
                    "output": {"firm_paybill": 1},
                },
                {
                    "name": "Case 2, variable-only input.",
                    "period": YEAR,
                    "input": {"firm_paybill": [1]},
                    "output": {"firm_paybill": [1]},
                },
            ]
        )
    )
    assert firms_block_cases(tmp_path) == ["nested/cases.yaml: Case 1, firms block."]


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def _build(system, situation):
    builder = SimulationBuilder()
    builder.set_default_period(YEAR)
    return builder.build_from_dict(system, situation)


def test_a_firms_block_beside_people_is_ignored_and_passes_vacuously(system):
    simulation = _build(system, {"people": {"adult": {"age": 40}}, "firms": FIRMS})
    paybill = simulation.calculate("firm_paybill", YEAR)
    assert simulation.populations["firm"].count == 0
    assert len(paybill) == 0
    # Why the guard is needed: the runner's comparison accepts any value.
    assert_near(paybill, 123_456_789, absolute_error_margin=0)


def test_a_firms_block_alone_is_rejected(system):
    with pytest.raises(SituationParsingError):
        _build(system, {"firms": FIRMS})


def test_variable_only_input_gives_one_firm_per_value(system):
    simulation = _build(system, {"firm_paybill": [1.0, 2.0]})
    assert simulation.populations["firm"].count == 2
    assert np.array_equal(simulation.calculate("firm_paybill", YEAR), [1.0, 2.0])
