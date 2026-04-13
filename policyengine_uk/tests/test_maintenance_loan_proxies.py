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
