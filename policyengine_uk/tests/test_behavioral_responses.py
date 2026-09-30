"""
Tests for behavioral labour supply responses.

Simulation.apply_dynamics applies the OBR labour supply responses when
gov.dynamic.obr_labour_supply_assumptions is on. These tests run it on small
household situations, so they need no survey data, and check that:
- it returns no responses when the OBR assumptions are off;
- with the OBR assumptions on but no policy change, every response and FTE
  impact is zero and employment income is unchanged;
- zero employment income and hours produce zero responses and FTE impacts
  rather than NaN;
- a real tax rise does produce responses, which change employment income by
  exactly the total response, and only for people who are not excluded (aged
  60 or over, self-employed, students, or beyond the first two adults in the
  household).
"""

import numpy as np
import pytest

from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario

YEAR = 2025
OBR_ASSUMPTIONS = "gov.dynamic.obr_labour_supply_assumptions"


def single_person(**person):
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


LABOUR_SUPPLY_CASES = [
    dict(
        name="parent with two children",
        obr=True,
        situation={
            "people": {
                "parent": {
                    "age": 30,
                    "employment_income": 20_000,
                    "hours_worked": 1500,
                },
                "child1": {"age": 5},
                "child2": {"age": 3},
            },
            "benunits": {"benunit": {"members": ["parent", "child1", "child2"]}},
            "households": {"household": {"members": ["parent", "child1", "child2"]}},
        },
    ),
    dict(
        name="married couple with two children",
        obr=True,
        situation={
            "people": {
                "adult1": {
                    "age": 35,
                    "employment_income": 25_000,
                    "hours_worked": 1800,
                    "gender": "MALE",
                },
                "adult2": {
                    "age": 33,
                    "employment_income": 18_000,
                    "hours_worked": 1200,
                    "gender": "FEMALE",
                },
                "child1": {"age": 6},
                "child2": {"age": 4},
            },
            "benunits": {
                "benunit": {
                    "members": ["adult1", "adult2", "child1", "child2"],
                    "is_married": True,
                }
            },
            "households": {
                "household": {"members": ["adult1", "adult2", "child1", "child2"]}
            },
        },
    ),
    dict(
        name="lone parent",
        obr=True,
        situation={
            "people": {
                "parent": {
                    "age": 28,
                    "employment_income": 12_000,
                    "hours_worked": 800,
                    "gender": "FEMALE",
                },
                "child1": {"age": 7},
                "child2": {"age": 4},
            },
            "benunits": {
                "benunit": {
                    "members": ["parent", "child1", "child2"],
                    "is_married": False,
                }
            },
            "households": {"household": {"members": ["parent", "child1", "child2"]}},
        },
    ),
    dict(
        name="OBR assumptions disabled",
        obr=False,
        situation=single_person(age=32, employment_income=15_000, hours_worked=1040),
    ),
    dict(
        name="high earner",
        obr=True,
        situation=single_person(age=50, employment_income=100_000, hours_worked=2200),
    ),
    dict(
        name="zero income and hours",
        obr=True,
        situation=single_person(age=30, employment_income=0, hours_worked=0),
    ),
]


def simulate_dynamics(situation, obr, parameter_changes=None):
    """Apply dynamics to a scenario that sets the OBR assumptions flag."""
    baseline = Microsimulation(situation=situation)
    changes = {OBR_ASSUMPTIONS: {str(YEAR): obr}, **(parameter_changes or {})}
    reformed = Microsimulation(
        situation=situation,
        scenario=Scenario(parameter_changes=changes),
    )
    reformed.baseline = baseline
    return reformed, reformed.apply_dynamics(YEAR)


class TestBehavioralResponses:
    """Test behavioral labour supply responses functionality"""

    @pytest.mark.parametrize(
        "parameter_path",
        [
            "gov.simulation.labour_supply_responses.income_elasticity",
            "gov.simulation.labor_supply_responses.income_elasticity",
        ],
    )
    def test_lsr_parameter_changes_accept_canonical_and_legacy_paths(
        self, parameter_path
    ):
        """Test that renamed LSR parameters still accept legacy reform paths."""
        scenario = Scenario(parameter_changes={parameter_path: {"2025": 0.123}})
        sim = Microsimulation(
            situation={
                "people": {"person": {"age": 30, "employment_income": 25_000}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            },
            scenario=scenario,
        )

        lsr = sim.tax_benefit_system.parameters.gov.simulation
        assert lsr.labour_supply_responses.income_elasticity("2025") == 0.123
        assert lsr.labor_supply_responses.income_elasticity("2025") == 0.123

    @pytest.mark.parametrize("obr", [True, False])
    def test_obr_parameter_functionality(self, obr):
        """Test that the OBR parameter can be enabled and disabled"""
        sim = Microsimulation(
            situation=single_person(age=30, employment_income=25_000),
            scenario=Scenario(parameter_changes={OBR_ASSUMPTIONS: {str(YEAR): obr}}),
        )
        assert (
            sim.tax_benefit_system.parameters.gov.dynamic.obr_labour_supply_assumptions(
                str(YEAR)
            )
            == obr
        )

    @pytest.mark.parametrize(
        "case", LABOUR_SUPPLY_CASES, ids=[case["name"] for case in LABOUR_SUPPLY_CASES]
    )
    def test_no_policy_change_gives_no_labour_supply_response(self, case):
        """Without a policy change, dynamics leave employment income unchanged."""
        reformed, dynamics = simulate_dynamics(case["situation"], case["obr"])

        if not case["obr"]:
            assert dynamics is None, "Dynamics should be None when OBR is disabled"
        else:
            assert dynamics is not None
            fte_impacts = dynamics.fte_impacts
            for impact in [
                fte_impacts.substitution_response_ftes,
                fte_impacts.income_response_ftes,
                fte_impacts.total_response_ftes,
                fte_impacts.ftes,
            ]:
                assert impact == 0
            responses = np.asarray(
                dynamics.progression[
                    ["substitution_response", "income_response", "total_response"]
                ],
                dtype=float,
            )
            assert (responses == 0).all(), responses
            # People without employment income have zero, not NaN, FTE responses.
            ftes = np.asarray(
                dynamics.progression[
                    [
                        "substitution_response_ftes",
                        "income_response_ftes",
                        "total_response_ftes",
                    ]
                ],
                dtype=float,
            )
            assert (ftes == 0).all(), ftes

        people = case["situation"]["people"].values()
        expected_income = [person.get("employment_income", 0) for person in people]
        np.testing.assert_array_equal(
            np.asarray(reformed.calculate("employment_income", YEAR)),
            expected_income,
        )

    def test_tax_rise_produces_labour_supply_response(self):
        """A basic rate rise moves labour supply, so dynamics are not inert."""
        situation = LABOUR_SUPPLY_CASES[1]["situation"]  # married couple
        reformed, dynamics = simulate_dynamics(
            situation,
            obr=True,
            parameter_changes={
                "gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}
            },
        )

        # Both adults have positive substitution and negative income
        # elasticities: a lower marginal wage cuts hours, lower net income
        # raises them.
        fte_impacts = dynamics.fte_impacts
        assert fte_impacts.substitution_response_ftes < 0
        assert fte_impacts.income_response_ftes > 0

        progression = dynamics.progression
        total_response = np.asarray(progression["total_response"], dtype=float)
        np.testing.assert_allclose(
            total_response,
            np.asarray(progression["substitution_response"], dtype=float)
            + np.asarray(progression["income_response"], dtype=float),
        )
        assert (total_response != 0).all()

        # Dynamics write each adult's response into employment income.
        employment_income = np.asarray(reformed.calculate("employment_income", YEAR))
        np.testing.assert_allclose(
            employment_income[:2],
            np.array([25_000, 18_000]) + total_response,
            rtol=1e-6,
        )
        np.testing.assert_array_equal(employment_income[2:], [0, 0])

    def test_excluded_people_get_no_labour_supply_response(self):
        """Only included adults' employment income moves under a tax rise."""
        people = ["grandparent", "adult1", "adult2", "child"]
        situation = {
            "people": {
                # Aged 60 or over, and adult 1 in the household by age.
                "grandparent": {
                    "age": 65,
                    "employment_income": 30_000,
                    "hours_worked": 1500,
                    "gender": "MALE",
                },
                # Adult 2: the only person included.
                "adult1": {
                    "age": 35,
                    "employment_income": 25_000,
                    "hours_worked": 1800,
                    "gender": "MALE",
                },
                # Adult 3: beyond the first two adults.
                "adult2": {
                    "age": 33,
                    "employment_income": 18_000,
                    "hours_worked": 1200,
                    "gender": "FEMALE",
                },
                "child": {"age": 4},
            },
            "benunits": {
                "grandparent_benunit": {"members": ["grandparent"]},
                "family": {
                    "members": ["adult1", "adult2", "child"],
                    "is_married": True,
                },
            },
            "households": {"household": {"members": people}},
        }
        reformed, dynamics = simulate_dynamics(
            situation,
            obr=True,
            parameter_changes={
                "gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}
            },
        )

        progression = dynamics.progression
        assert len(progression) == 1
        total_response = float(np.asarray(progression["total_response"])[0])
        assert total_response != 0

        employment_income = np.asarray(reformed.calculate("employment_income", YEAR))
        np.testing.assert_allclose(
            employment_income,
            [30_000, 25_000 + total_response, 18_000, 0],
            rtol=1e-6,
        )
