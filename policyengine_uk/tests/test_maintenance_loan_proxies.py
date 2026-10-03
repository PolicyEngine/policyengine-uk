from copy import deepcopy

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation


def test_maintenance_loan_in_higher_education_uses_prior_year_current_education():
    sim = Simulation(
        situation={
            "people": {
                "student": {
                    "age": {2024: 18, 2025: 19},
                    "current_education": {2024: "TERTIARY"},
                }
            },
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2025: "ENGLAND"}}
            },
        }
    )

    result = sim.calculate("maintenance_loan_in_higher_education", 2025)

    assert bool(result[0]) is True


def test_maintenance_loan_in_higher_education_uses_current_year_in_he():
    sim = Simulation(
        situation={
            "people": {
                "student": {
                    "age": {2025: 19},
                    "in_HE": {2025: True},
                }
            },
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2025: "ENGLAND"}}
            },
        }
    )

    result = sim.calculate("maintenance_loan_in_higher_education", 2025)

    assert bool(result[0]) is True


def test_maintenance_loan_current_year_current_education_overrides_in_he():
    sim = Simulation(
        situation={
            "people": {
                "student": {
                    "age": {2025: 19},
                    "current_education": {2025: "POST_SECONDARY"},
                    "in_HE": {2025: True},
                }
            },
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2025: "ENGLAND"}}
            },
        }
    )

    result = sim.calculate("maintenance_loan_in_higher_education", 2025)

    assert bool(result[0]) is False


def test_maintenance_loan_in_higher_education_uses_prior_year_in_he():
    sim = Simulation(
        situation={
            "people": {
                "student": {
                    "age": {2024: 18, 2025: 19},
                    "in_HE": {2024: True},
                }
            },
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2025: "ENGLAND"}}
            },
        }
    )

    result = sim.calculate("maintenance_loan_in_higher_education", 2025)

    assert bool(result[0]) is True


def test_maintenance_loan_in_higher_education_handles_mixed_population_inputs():
    sim = Simulation(
        situation={
            "people": {
                "student_with_current_education": {
                    "age": {2025: 19},
                    "current_education": {2025: "TERTIARY"},
                },
                "student_with_in_he": {
                    "age": {2025: 19},
                    "in_HE": {2025: True},
                },
            },
            "benunits": {
                "benunit_1": {"members": ["student_with_current_education"]},
                "benunit_2": {"members": ["student_with_in_he"]},
            },
            "households": {
                "household": {
                    "members": [
                        "student_with_current_education",
                        "student_with_in_he",
                    ],
                    "country": {2025: "ENGLAND"},
                }
            },
        }
    )

    result = sim.calculate("maintenance_loan_in_higher_education", 2025)

    assert bool(result[0]) is True
    assert bool(result[1]) is True


# Explicit evidence means entered values. These checks used to ask whether a
# value was stored, which is true once anything has calculated the variable,
# so the answer depended on what had been calculated first.

PARENTAL_HOUSEHOLD = {
    "people": {
        "parent": {
            "age": {2025: 52},
            "current_education": {2025: "NOT_IN_EDUCATION"},
            "adjusted_net_income": {2025: 30_000},
            "is_household_head": {2025: True},
        },
        "student": {
            "age": {2025: 20},
            "current_education": {2025: "TERTIARY"},
            "adjusted_net_income": {2025: 2_000},
            "is_household_head": {2025: False},
        },
    },
    "benunits": {
        "parent_benunit": {"members": ["parent"]},
        "student_benunit": {"members": ["student"]},
    },
    "households": {
        "household": {
            "members": ["parent", "student"],
            "country": {2025: "ENGLAND"},
            "region": {2025: "NORTH_WEST"},
        }
    },
}


@pytest.mark.parametrize(
    "first",
    [(), ("tenure_type",), ("benunit_is_renting",), ("housing_benefit",)],
)
def test_the_default_tenure_is_not_evidence_of_renting_in_any_order(first):
    # No tenure is entered, so the proxy must not read the default
    # (RENT_PRIVATELY) as renting, even after something has calculated it.
    sim = Simulation(situation=PARENTAL_HOUSEHOLD)
    for variable in first:
        sim.calculate(variable, 2025)
    assert list(sim.calculate("maintenance_loan_living_arrangement", 2025)) == [
        "AWAY_OUTSIDE_LONDON",
        "LIVING_WITH_PARENTS",
    ]
    assert list(sim.calculate("maintenance_loan_household_income", 2025)) == [
        30_000,
        32_000,
    ]


def test_an_entered_tenure_carries_forward_as_evidence():
    situation = deepcopy(PARENTAL_HOUSEHOLD)
    situation["households"]["household"]["tenure_type"] = {2024: "RENT_PRIVATELY"}
    sim = Simulation(situation=situation)
    assert list(sim.calculate("maintenance_loan_living_arrangement", 2025)) == [
        "AWAY_OUTSIDE_LONDON",
        "AWAY_OUTSIDE_LONDON",
    ]


@pytest.mark.parametrize("first", [(), ("current_education",), ("child_benefit",)])
def test_age_based_enrolment_is_not_higher_education_evidence_in_any_order(first):
    # A 19-year-old with no education input is imputed TERTIARY by
    # current_education; that fallback is not evidence, whether or not it
    # has been calculated already.
    sim = Simulation(
        situation={
            "people": {"student": {"age": {2025: 19}}},
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2025: "ENGLAND"}}
            },
        }
    )
    for variable in first:
        sim.calculate(variable, 2025)
    assert bool(sim.calculate("maintenance_loan_in_higher_education", 2025)[0]) is False


@pytest.mark.parametrize("first", [(), (2025,), (2027, 2025)])
def test_prior_year_evidence_is_the_latest_entered_year(first):
    # current_education was entered for 2024 only. 2026's prior-year evidence
    # is that entry, whether or not 2025 has been calculated.
    sim = Simulation(
        situation={
            "people": {
                "student": {
                    "age": {2024: 18, 2025: 19, 2026: 20},
                    "current_education": {2024: "TERTIARY"},
                }
            },
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2026: "ENGLAND"}}
            },
        }
    )
    for year in first:
        sim.calculate("current_education", year)
        sim.calculate("maintenance_loan_in_higher_education", year)
    assert bool(sim.calculate("maintenance_loan_in_higher_education", 2026)[0]) is True


def test_current_year_in_he_outranks_an_earlier_enrolment():
    # The documented order: current-year in_HE comes before prior-year
    # current_education, including one carried forward from an earlier year.
    sim = Simulation(
        situation={
            "people": {
                "student": {
                    "age": {2024: 18, 2025: 19},
                    "current_education": {2024: "POST_SECONDARY"},
                    "in_HE": {2025: True},
                }
            },
            "benunits": {"benunit": {"members": ["student"]}},
            "households": {
                "household": {"members": ["student"], "country": {2025: "ENGLAND"}}
            },
        }
    )
    sim.calculate("current_education", 2025)
    assert bool(sim.calculate("maintenance_loan_in_higher_education", 2025)[0]) is True


PROXY_OUTPUTS = (
    "maintenance_loan_in_higher_education",
    "maintenance_loan_living_arrangement",
    "maintenance_loan_household_income",
)
PRIOR_CALCULATIONS = (
    "current_education",
    "in_HE",
    "tenure_type",
    "benunit_is_renting",
    *PROXY_OUTPUTS,
)


def proxy_situation(student_inputs, tenure):
    situation = deepcopy(PARENTAL_HOUSEHOLD)
    student = situation["people"]["student"]
    student["age"] = {year: 20 for year in range(2023, 2029)}
    del student["current_education"]
    student.update(student_inputs)
    if tenure is not None:
        situation["households"]["household"]["tenure_type"] = tenure
    return situation


@settings(max_examples=20, deadline=None, derandomize=True)
@given(
    student_inputs=st.fixed_dictionaries(
        {},
        optional={
            "current_education": st.dictionaries(
                st.sampled_from(range(2024, 2027)),
                st.sampled_from(["TERTIARY", "POST_SECONDARY", "NOT_IN_EDUCATION"]),
                max_size=2,
            ),
            "in_HE": st.dictionaries(
                st.sampled_from(range(2024, 2027)), st.booleans(), max_size=2
            ),
        },
    ),
    tenure=st.one_of(
        st.none(),
        st.dictionaries(
            st.sampled_from(range(2024, 2027)),
            st.sampled_from(["RENT_PRIVATELY", "OWNED_OUTRIGHT"]),
            min_size=1,
            max_size=2,
        ),
    ),
    first=st.lists(
        st.tuples(
            st.sampled_from(PRIOR_CALCULATIONS), st.sampled_from(range(2024, 2028))
        ),
        max_size=5,
    ),
    target=st.sampled_from(range(2025, 2028)),
)
def test_proxy_outputs_do_not_depend_on_what_was_calculated_first(
    student_inputs, tenure, first, target
):
    situation = proxy_situation(student_inputs, tenure)
    fresh = Simulation(situation=situation)
    ordered = Simulation(situation=situation)
    for variable, year in first:
        ordered.calculate(variable, year)
    for variable in PROXY_OUTPUTS:
        assert np.array_equal(
            np.asarray(fresh.calculate(variable, target)),
            np.asarray(ordered.calculate(variable, target)),
        ), variable
