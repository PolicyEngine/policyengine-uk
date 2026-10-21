"""Regression tests for `claims_all_entitled_benefits`.

The flag is a benefit-unit attribute: a family that reports under £1 in total
across the seven means-tested benefits the formula checks is assumed to claim
everything it is entitled to, and a family that reports £1 or more is assumed
to have reported completely. The formula used to sum the seven reported columns over the whole
simulation (`add(...).sum() < 1`), so in microdata it was False for every
benefit unit as soon as any benefit unit reported any of them, and the
consumers that gate on it collapsed to reporters only. Hand-entered situations
now test each family on its own. Data-built simulations keep main's survey
result, False for every family, so Child Tax Credit, Working Tax Credit and
Income Support take-up follow reported claims there; Council Tax Reduction and
Housing Benefit are reporters-only on data-built simulations in any case
(d1390 and d1455).
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import example, given, settings, strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026

SEVEN_REPORTED = [
    "child_tax_credit_reported",
    "working_tax_credit_reported",
    "universal_credit_reported",
    "housing_benefit_reported",
    "jsa_income_reported",
    "income_support_reported",
    "esa_income_reported",
]


def person(reported_uc=0, reported_ctr=0):
    return {
        "age": {YEAR: 40},
        "universal_credit_reported": {YEAR: reported_uc},
        "council_tax_benefit_reported": {YEAR: reported_ctr},
    }


def single_household(reported_uc):
    """One person, one benefit unit, one household — the calculator path."""
    return {
        "people": {"a": person(reported_uc)},
        "benunits": {"bu_a": {"members": ["a"]}},
        "households": {"hh_a": {"members": ["a"]}},
    }


def separate_households(reported_uc_a, reported_uc_b):
    """Two benefit units in two households; `a` is index 0, `b` index 1."""
    return {
        "people": {"a": person(reported_uc_a), "b": person(reported_uc_b)},
        "benunits": {"bu_a": {"members": ["a"]}, "bu_b": {"members": ["b"]}},
        "households": {"hh_a": {"members": ["a"]}, "hh_b": {"members": ["b"]}},
    }


def shared_household(reported_uc_a, reported_uc_b):
    """Two benefit units sharing one household (e.g. a parent and an adult child)."""
    return {
        "people": {"a": person(reported_uc_a), "b": person(reported_uc_b)},
        "benunits": {"bu_a": {"members": ["a"]}, "bu_b": {"members": ["b"]}},
        "households": {"hh": {"members": ["a", "b"]}},
    }


class TestPerBenefitUnit:
    def test_one_reporter_does_not_switch_off_the_other_benefit_unit(self):
        sim = Simulation(situation=separate_households(5_000, 0))
        flag = sim.calculate("claims_all_entitled_benefits", YEAR)
        assert flag.tolist() == [False, True]

    def test_per_benefit_unit_within_one_household(self):
        sim = Simulation(situation=shared_household(5_000, 0))
        flag = sim.calculate("claims_all_entitled_benefits", YEAR)
        assert flag.tolist() == [False, True]

    def test_situation_ctr_default_follows_each_familys_flag(self):
        sim = Simulation(situation=separate_households(5_000, 0))
        would_claim = sim.calculate("would_claim_council_tax_reduction", YEAR)
        assert would_claim.tolist() == [False, True]

    def test_reported_ctr_still_claims_when_the_flag_is_false(self):
        situation = separate_households(5_000, 0)
        situation["people"]["a"] = person(reported_uc=5_000, reported_ctr=800)
        sim = Simulation(situation=situation)
        assert sim.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
            False,
            True,
        ]
        assert sim.calculate("would_claim_council_tax_reduction", YEAR).tolist() == [
            True,
            True,
        ]

    def test_reporters_of_any_of_the_seven_are_false(self):
        for variable in SEVEN_REPORTED:
            situation = separate_households(0, 0)
            situation["people"]["a"][variable] = {YEAR: 100}
            sim = Simulation(situation=situation)
            flag = sim.calculate("claims_all_entitled_benefits", YEAR)
            assert flag.tolist() == [False, True], variable

    def test_single_benefit_unit_semantics_unchanged(self):
        none_reported = Simulation(situation=single_household(0))
        assert none_reported.calculate(
            "claims_all_entitled_benefits", YEAR
        ).tolist() == [True]
        reporter = Simulation(situation=single_household(5_000))
        assert reporter.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
            False
        ]

    def test_homogeneous_benefit_units_agree(self):
        none_reported = Simulation(situation=separate_households(0, 0))
        assert none_reported.calculate("claims_all_entitled_benefits", YEAR).all()
        both_report = Simulation(situation=separate_households(5_000, 5_000))
        assert not both_report.calculate("claims_all_entitled_benefits", YEAR).any()

    def test_under_one_pound_of_reported_benefits_counts_as_none(self):
        sim = Simulation(situation=separate_households(0.5, 0))
        assert sim.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
            True,
            True,
        ]


@pytest.mark.microsimulation
def test_survey_takeup_follows_reports_in_microdata():
    """On the survey the flag keeps main's value, false for every family, so
    the legacy take-up flags that read it are reporters only (review r6)."""
    sim = Microsimulation()
    for year in (2024, YEAR):
        flag = sim.calculate("claims_all_entitled_benefits", year).values
        assert not flag.astype(bool).any(), year
        for takeup, reported in (
            ("would_claim_CTC", "child_tax_credit_reported"),
            ("would_claim_WTC", "working_tax_credit_reported"),
        ):
            reports = sim.calculate(reported, year, map_to="benunit").values > 0
            claims = sim.calculate(takeup, year).values.astype(bool)
            assert np.array_equal(claims, reports), (takeup, year)
        is_reports = (
            sim.calculate("income_support_reported", year).values
            * sim.calculate("is_claimant_or_partner", year).values
        )
        reported_is = sim.map_result(is_reports, "person", "benunit") > 0
        claims_is = sim.calculate("would_claim_IS", year).values.astype(bool)
        assert np.array_equal(claims_is, reported_is), year


def mock_dataset(situation, year=YEAR):
    """Synthetic post-ingestion MOCK tables using the normal UK data schema."""
    tables = {}
    person_ids = {name: i + 1 for i, name in enumerate(situation["people"])}
    memberships = {}
    for plural, entity in (
        ("people", "person"),
        ("benunits", "benunit"),
        ("households", "household"),
    ):
        rows = []
        for index, (_, inputs) in enumerate(situation[plural].items(), start=1):
            row = {f"{entity}_id": index}
            for name, value in inputs.items():
                if name == "members":
                    for member in value:
                        memberships.setdefault(person_ids[member], {})[
                            f"person_{entity}_id"
                        ] = index
                else:
                    row[name] = value[year] if isinstance(value, dict) else value
            rows.append(row)
        tables[entity] = pd.DataFrame(rows).fillna(0)
    for column in ("person_benunit_id", "person_household_id"):
        tables["person"][column] = [
            memberships[person_id][column] for person_id in person_ids.values()
        ]
    return UKMultiYearDataset(
        datasets=[UKSingleYearDataset(**tables, fiscal_year=year)]
    )


def pensioner_households():
    situation = separate_households(0, 0)
    for person_inputs in situation["people"].values():
        person_inputs["age"] = {YEAR: 70}
    for home in situation["households"].values():
        home.update(
            region={YEAR: "NORTH_WEST"},
            tenure_type={YEAR: "RENT_PRIVATELY"},
            rent={YEAR: 8_000},
            council_tax={YEAR: 1_800},
        )
    return situation


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
@pytest.mark.parametrize(
    "takeup, reported, benefit, expected_award",
    [
        (
            "would_claim_council_tax_reduction",
            "council_tax_benefit_reported",
            "council_tax_reduction",
            1_800,
        ),
        (
            "would_claim_housing_benefit",
            "housing_benefit_reported",
            "housing_benefit",
            8_000,
        ),
    ],
)
def test_mock_data_takeup_is_reporters_only(
    simulation_class, takeup, reported, benefit, expected_award
):
    situation = pensioner_households()
    situation["people"]["b"][reported] = {YEAR: 100}
    simulation = simulation_class(dataset=mock_dataset(situation))
    assert simulation.calculate(takeup, YEAR).tolist() == [False, True]
    np.testing.assert_allclose(simulation.calculate(benefit, YEAR), [0, expected_award])
    # The non-reporter is entitled: an explicit input enables its award.
    for family in situation["benunits"].values():
        family[takeup] = {YEAR: True}
    explicit = simulation_class(dataset=mock_dataset(situation))
    np.testing.assert_allclose(
        explicit.calculate(benefit, YEAR), [expected_award, expected_award]
    )


def test_hand_entered_housing_benefit_keeps_main_takeup():
    simulation = Simulation(situation=pensioner_households())
    assert simulation.calculate("would_claim_housing_benefit", YEAR).tolist() == [
        True,
        True,
    ]
    np.testing.assert_allclose(
        simulation.calculate("housing_benefit", YEAR), [8_000, 8_000]
    )


@pytest.mark.parametrize(
    "reported",
    [
        "pension_credit_reported",
        "child_benefit_reported",
        "council_tax_benefit_reported",
    ],
)
def test_reports_outside_the_seven_leave_the_all_benefits_flag_true(reported):
    situation = separate_households(0, 0)
    situation["people"]["a"][reported] = {YEAR: 100}
    simulation = Simulation(situation=situation)
    assert simulation.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
        True,
        True,
    ]


# Each generated family is independently eligible or ineligible and may have
# reported CTR. No explicit take-up column is supplied; other families cannot enable it.
CTR_FAMILIES = st.lists(
    st.tuples(
        st.integers(min_value=18, max_value=90),
        st.sampled_from(("ENGLAND", "SCOTLAND", "WALES")),
        st.integers(min_value=0, max_value=50_000),
        st.integers(min_value=0, max_value=50_000),
        st.booleans(),
        st.sampled_from((0, 100)),
    ),
    min_size=1,
    max_size=4,
)


@given(families=CTR_FAMILIES)
@example(families=[(40, "SCOTLAND", 0, 0, True, 0)])
@example(
    families=[
        (40, "WALES", 0, 0, True, 0),
        (40, "WALES", 0, 0, True, 100),
        (70, "ENGLAND", 0, 0, False, 100),
    ]
)
@settings(max_examples=30, deadline=None)
def test_ctr_is_zero_for_every_nonreporter_without_an_explicit_claim_flag(families):
    situation = {"people": {}, "benunits": {}, "households": {}}
    must_be_zero = []
    councils = {
        "ENGLAND": "MAIDSTONE",
        "SCOTLAND": "CITY_OF_EDINBURGH",
        "WALES": "CARDIFF",
    }
    for index, (age, country, income, savings, claims_all, reported) in enumerate(
        families
    ):
        name = f"person_{index}"
        situation["people"][name] = {
            "age": {YEAR: age},
            "employment_income": {YEAR: income},
            "council_tax_benefit_reported": {YEAR: reported},
        }
        benunit = {
            "members": [name],
            "claims_all_entitled_benefits": {YEAR: claims_all},
            "would_claim_uc": {YEAR: False},
        }
        situation["benunits"][f"bu_{index}"] = benunit
        situation["households"][f"hh_{index}"] = {
            "members": [name],
            "country": {YEAR: country},
            "local_authority": {YEAR: councils[country]},
            "council_tax": {YEAR: 1_800},
            "savings": {YEAR: savings},
        }
        must_be_zero.append(reported == 0)
    sim = Simulation(dataset=mock_dataset(situation))
    mask = np.array(must_be_zero, dtype=bool)
    assert not sim.calculate("would_claim_council_tax_reduction", YEAR)[mask].any()
    for variable in (
        "simulated_council_tax_reduction_benunit",
        "council_tax_benefit",
        "council_tax_reduction",
    ):
        assert (sim.calculate(variable, YEAR)[mask] == 0).all(), variable


# Tax credits pay awards until 5 April 2025, so 2024 is a year in which the
# legacy take-up flags still reach an award.
TAX_CREDIT_YEAR = 2024


def tax_credit_families():
    """Review r6's MOCK probe: a non-reporting lone parent and a non-reporting
    working pensioner, beside a family that reports Child Tax Credit and CTR."""
    year = TAX_CREDIT_YEAR
    renting = {
        "region": {year: "NORTH_WEST"},
        "tenure_type": {year: "RENT_PRIVATELY"},
        "rent": {year: 8_000},
        "council_tax": {year: 1_800},
    }
    return {
        "people": {
            "parent": {
                "age": {year: 30},
                "employment_income": {year: 12_000},
                "weekly_hours": {year: 20},
            },
            "child": {"age": {year: 5}},
            "pensioner": {
                "age": {year: 68},
                "employment_income": {year: 9_000},
                "weekly_hours": {year: 20},
            },
            "reporter": {
                "age": {year: 35},
                "employment_income": {year: 12_000},
                "weekly_hours": {year: 20},
                "child_tax_credit_reported": {year: 3_000},
                "council_tax_benefit_reported": {year: 500},
            },
            "reporter_child": {"age": {year: 6}},
        },
        "benunits": {
            "bu_parent": {
                "members": ["parent", "child"],
                "would_claim_uc": {year: False},
            },
            "bu_pensioner": {
                "members": ["pensioner"],
                "would_claim_uc": {year: False},
            },
            "bu_reporter": {
                "members": ["reporter", "reporter_child"],
                "would_claim_uc": {year: False},
            },
        },
        "households": {
            "hh_parent": {"members": ["parent", "child"], **renting},
            "hh_pensioner": {
                "members": ["pensioner"],
                "region": {year: "NORTH_WEST"},
                "tenure_type": {year: "OWNED_OUTRIGHT"},
                "council_tax": {year: 1_800},
            },
            "hh_reporter": {"members": ["reporter", "reporter_child"], **renting},
        },
    }


def test_data_built_nonreporters_get_no_tax_credits():
    """Survey runs keep main's take-up for tax credits (review r6). Tested per
    family on data, the lone parent's flag turned true, so would_claim_CTC
    did too, and £3,455 of tax credits reached its CTR and HB means tests,
    its tax credit award and the 2024 Winter Fuel Payment benefit test."""
    year = TAX_CREDIT_YEAR
    situation = tax_credit_families()
    data = Simulation(dataset=mock_dataset(situation, year))
    assert data.calculate("claims_all_entitled_benefits", year).tolist() == [
        False,
        False,
        False,
    ]
    assert data.calculate("would_claim_CTC", year).tolist() == [False, False, True]
    for takeup in ("would_claim_WTC", "would_claim_IS"):
        assert not data.calculate(takeup, year).any(), takeup
    tax_credits = data.calculate("tax_credits", year)
    assert tax_credits[:2].tolist() == [0, 0]
    assert tax_credits[2] > 0
    # People: parent, child, pensioner, reporter, reporter_child.
    assert data.calculate("tax_credit_award", year)[0] == 0
    assert not data.calculate("is_on_winter_fuel_payment_relevant_benefit", year)[0]
    # The same families entered by hand keep the per-family flag.
    hand = Simulation(situation=situation)
    assert hand.calculate("claims_all_entitled_benefits", year).tolist() == [
        True,
        True,
        False,
    ]


# Each take-up flag that reads claims_all_entitled_benefits, and the report
# that sets it on data-built simulations.
TAKEUP_REPORTS = {
    "would_claim_CTC": "child_tax_credit_reported",
    "would_claim_WTC": "working_tax_credit_reported",
    "would_claim_IS": "income_support_reported",
    "would_claim_housing_benefit": "housing_benefit_reported",
    "would_claim_council_tax_reduction": "council_tax_benefit_reported",
}

# Outputs downstream of the take-up flags: tax credits, their award and the
# means tests and benefit tests that read them, and household net income.
TAKEUP_OUTPUTS = (
    "tax_credits",
    "child_tax_credit",
    "working_tax_credit",
    "income_support",
    "housing_benefit",
    "council_tax_reduction",
    "council_tax_reduction_applicable_income",
    "housing_benefit_applicable_income",
    "tax_credit_award",
    "is_on_winter_fuel_payment_relevant_benefit",
    "household_net_income",
)

LEGACY_FAMILIES = st.lists(
    st.fixed_dictionaries(
        {
            "age": st.integers(min_value=18, max_value=80),
            "children": st.integers(min_value=0, max_value=2),
            "earnings": st.integers(min_value=0, max_value=40_000),
            "hours": st.sampled_from((0, 10, 20, 35)),
            "renter": st.booleans(),
            "reports": st.frozensets(
                st.sampled_from(SEVEN_REPORTED + ["council_tax_benefit_reported"])
            ),
        }
    ),
    min_size=1,
    max_size=3,
)


def legacy_families(families, year, takeup=None):
    """One benefit unit and household per family; the adult reports £100 of
    each benefit in `reports`. `takeup` adds explicit take-up columns."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, family in enumerate(families):
        adult = f"adult_{index}"
        members = [adult]
        situation["people"][adult] = {
            "age": {year: family["age"]},
            "employment_income": {year: family["earnings"]},
            "weekly_hours": {year: family["hours"]},
            **{report: {year: 100} for report in sorted(family["reports"])},
        }
        for child in range(family["children"]):
            name = f"child_{index}_{child}"
            situation["people"][name] = {"age": {year: 4 + child}}
            members.append(name)
        benunit = {"members": members}
        for variable, values in (takeup or {}).items():
            benunit[variable] = {year: bool(values[index])}
        situation["benunits"][f"bu_{index}"] = benunit
        situation["households"][f"hh_{index}"] = {
            "members": members,
            "region": {year: "NORTH_WEST"},
            "tenure_type": {
                year: "RENT_PRIVATELY" if family["renter"] else "OWNED_OUTRIGHT"
            },
            "rent": {year: 8_000 if family["renter"] else 0},
            "council_tax": {year: 1_800},
        }
    return situation


NO_REPORTS = dict(age=30, children=1, earnings=12_000, hours=20, renter=True)


@given(families=LEGACY_FAMILIES, year=st.sampled_from((TAX_CREDIT_YEAR, YEAR)))
# No family reports anything: main's simulation-wide sum set every flag true
# here, so this example differs from main by design (reports-only on data).
@example(families=[{**NO_REPORTS, "reports": frozenset()}], year=TAX_CREDIT_YEAR)
@example(
    families=[
        {**NO_REPORTS, "reports": frozenset()},
        {
            **NO_REPORTS,
            "reports": frozenset(
                {"child_tax_credit_reported", "council_tax_benefit_reported"}
            ),
        },
    ],
    year=TAX_CREDIT_YEAR,
)
@settings(max_examples=10, deadline=None)
def test_data_built_takeup_equals_reported_only(families, year):
    """On data, every take-up flag that reads claims_all_entitled_benefits is
    the family's own report, and every downstream output equals the same data
    with those reported-only take-up flags given as explicit inputs."""
    reported = {
        takeup: [report in family["reports"] for family in families]
        for takeup, report in TAKEUP_REPORTS.items()
    }
    default = Simulation(dataset=mock_dataset(legacy_families(families, year), year))
    explicit = Simulation(
        dataset=mock_dataset(legacy_families(families, year, reported), year)
    )
    assert not default.calculate("claims_all_entitled_benefits", year).any()
    for takeup, expected in reported.items():
        assert default.calculate(takeup, year).tolist() == expected, takeup
    for variable in TAKEUP_OUTPUTS:
        np.testing.assert_array_equal(
            default.calculate(variable, year),
            explicit.calculate(variable, year),
            err_msg=variable,
        )
