"""Tests for deterministic stochastic variables.

These tests verify that variables which previously used random() now:
1. Use default values correctly in policy calculator mode (no dataset)
2. Can be set explicitly in situations
3. Produce deterministic results
"""

import pytest
from policyengine_uk import Simulation


class TestDefaultValues:
    """Test that stochastic variables have correct default values."""

    def test_would_claim_child_benefit_defaults_true(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_claim_child_benefit", 2024)
        assert result[0] == True

    def test_would_claim_uc_defaults_true(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_claim_uc", 2024)
        assert result[0] == True

    def test_would_claim_pc_defaults_true(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 70}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_claim_pc", 2024)
        assert result[0] == True

    def test_household_owns_tv_defaults_true(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("household_owns_tv", 2024)
        assert result[0] == True

    def test_would_evade_tv_licence_fee_defaults_false(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_evade_tv_licence_fee", 2024)
        assert result[0] == False

    def test_is_disabled_for_benefits_defaults_false(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("is_disabled_for_benefits", 2024)
        assert result[0] == False

    def test_would_claim_marriage_allowance_defaults_true(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_claim_marriage_allowance", 2024)
        assert result[0] == True

    def test_child_benefit_opts_out_defaults_false(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("child_benefit_opts_out", 2024)
        assert result[0] == False


class TestExplicitOverrides:
    """Test that stochastic variables can be set explicitly."""

    def test_would_claim_child_benefit_can_be_set_false(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {
                    "benunit": {
                        "members": ["person"],
                        "would_claim_child_benefit": {2024: False},
                    }
                },
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_claim_child_benefit", 2024)
        assert result[0] == False

    def test_would_claim_uc_can_be_set_false(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {
                    "benunit": {
                        "members": ["person"],
                        "would_claim_uc": {2024: False},
                    }
                },
                "households": {"household": {"members": ["person"]}},
            }
        )
        result = sim.calculate("would_claim_uc", 2024)
        assert result[0] == False

    def test_household_owns_tv_can_be_set_false(self):
        sim = Simulation(
            situation={
                "people": {"person": {"age": {2024: 30}}},
                "benunits": {"benunit": {"members": ["person"]}},
                "households": {
                    "household": {
                        "members": ["person"],
                        "household_owns_tv": {2024: False},
                    }
                },
            }
        )
        result = sim.calculate("household_owns_tv", 2024)
        assert result[0] == False


class TestIsHigherEarner:
    """Test deterministic tie-breaking for is_higher_earner."""

    def test_higher_income_wins(self):
        """Person with higher income should be the higher earner."""
        sim = Simulation(
            situation={
                "people": {
                    "person1": {
                        "age": {2024: 30},
                        "employment_income": {2024: 60000},
                    },
                    "person2": {
                        "age": {2024: 40},
                        "employment_income": {2024: 50000},
                    },
                },
                "benunits": {"benunit": {"members": ["person1", "person2"]}},
                "households": {
                    "household": {"members": ["person1", "person2"]}
                },
            }
        )
        result = sim.calculate("is_higher_earner", 2024)
        # person1 has higher income, should be True
        assert result[0] == True
        # person2 has lower income, should be False
        assert result[1] == False

    def test_same_income_older_wins(self):
        """With same income, older person should be the higher earner."""
        sim = Simulation(
            situation={
                "people": {
                    "person1": {
                        "age": {2024: 40},
                        "employment_income": {2024: 50000},
                    },
                    "person2": {
                        "age": {2024: 30},
                        "employment_income": {2024: 50000},
                    },
                },
                "benunits": {"benunit": {"members": ["person1", "person2"]}},
                "households": {
                    "household": {"members": ["person1", "person2"]}
                },
            }
        )
        result = sim.calculate("is_higher_earner", 2024)
        # person1 is older, should win the tie
        assert result[0] == True
        # person2 is younger, should lose the tie
        assert result[1] == False

    def test_is_deterministic(self):
        """Same inputs should always produce same outputs."""
        situation = {
            "people": {
                "person1": {
                    "age": {2024: 35},
                    "employment_income": {2024: 50000},
                },
                "person2": {
                    "age": {2024: 35},
                    "employment_income": {2024: 50000},
                },
            },
            "benunits": {"benunit": {"members": ["person1", "person2"]}},
            "households": {"household": {"members": ["person1", "person2"]}},
        }

        results = []
        for _ in range(3):
            sim = Simulation(situation=situation)
            results.append(tuple(sim.calculate("is_higher_earner", 2024)))

        # All results should be identical
        assert results[0] == results[1] == results[2]


class TestDeterminism:
    """Test that calculations are deterministic across runs."""

    def test_child_benefit_is_deterministic(self):
        """Child benefit calculation should be deterministic."""
        situation = {
            "people": {
                "adult": {"age": {2024: 30}},
                "child": {"age": {2024: 5}},
            },
            "benunits": {
                "benunit": {
                    "members": ["adult", "child"],
                    "would_claim_child_benefit": {2024: True},
                }
            },
            "households": {"household": {"members": ["adult", "child"]}},
        }

        results = []
        for _ in range(3):
            sim = Simulation(situation=situation)
            results.append(float(sim.calculate("child_benefit", 2024)[0]))

        assert results[0] == results[1] == results[2]

    def test_marriage_allowance_is_deterministic(self):
        """Marriage allowance should be deterministic."""
        situation = {
            "people": {
                "person1": {
                    "age": {2024: 35},
                    "marital_status": {2024: "MARRIED"},
                    "employment_income": {2024: 20000},
                },
                "person2": {
                    "age": {2024: 35},
                    "marital_status": {2024: "MARRIED"},
                    "employment_income": {2024: 50000},
                },
            },
            "benunits": {"benunit": {"members": ["person1", "person2"]}},
            "households": {"household": {"members": ["person1", "person2"]}},
        }

        results = []
        for _ in range(3):
            sim = Simulation(situation=situation)
            results.append(tuple(sim.calculate("marriage_allowance", 2024)))

        assert results[0] == results[1] == results[2]
