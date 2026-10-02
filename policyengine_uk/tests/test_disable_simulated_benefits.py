"""disable_simulated_benefits pays each family the benefits it reported.

The reform (gov.contrib.policyengine.disable_simulated_benefits) sets each
listed benefit, in the dataset year and the nine years after it, to the
amount reported in the dataset year. The *_reported variables are uprated, so
in a later year a stored esa_income or jsa_income equals neither the award on
that year's reports nor their plain total. Read by value alone, it would then
be taken to be wholly the claimant's or partner's, another member's award
included. So the reform also sets the claimant's and partner's awards
(claimant_or_partner_esa_income, claimant_or_partner_jsa_income) for each
year, from their own reports in the dataset year, and Income Support from
theirs alone. Both of Income Support's income-related limbs (SSCBA 1992
s.124(1)(f) and (h)) and the council tax reduction passport read those
awards.

Each family below is its own benefit unit and household. Reported amounts are
entered for the dataset year only, so later years uprate them. Everything
else is entered for every year.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.reforms.policyengine.disable_simulated_benefits import (
    BENEFITS,
    CLAIMANT_OR_PARTNER_AWARDS,
    CLAIMANT_OR_PARTNER_ONLY,
    PRE_MINIMUM,
    YEARS_IN_FUTURE,
)
from policyengine_uk.utils.benefit_unit import claimant_or_partner_award
from policyengine_uk.utils.scenario import Scenario
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award

DATASET_YEAR = 2025
# The dataset year and two later years.
YEARS = [DATASET_YEAR, DATASET_YEAR + 1, DATASET_YEAR + 2]

REFORM = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.policyengine.disable_simulated_benefits": True},
)


def every_year(value):
    return {year: value for year in YEARS}


def adult(age, claimant_or_partner, carer=False, **reported):
    person = {
        "age": every_year(age),
        "is_claimant_or_partner": every_year(claimant_or_partner),
        "receives_carer_benefit": every_year(carer),
        "current_education": every_year("NOT_IN_EDUCATION"),
    }
    for name, amount in reported.items():
        person[name] = {DATASET_YEAR: amount}
    return person


# A carer who reports Income Support satisfies every other condition of
# income_support_eligible, so in these families only the income-related
# limbs can bar the claim.
CARER = dict(age=40, claimant_or_partner=True, carer=True)
NOT_IN_COUPLE = dict(age=30, claimant_or_partner=False)

# family: (members, capital)
FAMILIES = {
    # An adult outside the couple, such as a non-dependent, claims ESA and
    # JSA in their own right.
    "excluded_adult": (
        [
            adult(**CARER, income_support_reported=1_000),
            adult(
                **NOT_IN_COUPLE, esa_income_reported=3_000, jsa_income_reported=2_000
            ),
        ],
        0,
    ),
    # The same, with no Income Support award to passport the claimant.
    "excluded_adult_no_award": (
        [
            adult(age=40, claimant_or_partner=True),
            adult(
                **NOT_IN_COUPLE, esa_income_reported=3_000, jsa_income_reported=2_000
            ),
        ],
        0,
    ),
    # The claimant's own income-related ESA.
    "own_esa": (
        [adult(**CARER, income_support_reported=1_000, esa_income_reported=3_000)],
        0,
    ),
    # The claimant's own income-based JSA.
    "own_jsa": (
        [adult(**CARER, income_support_reported=1_000, jsa_income_reported=2_000)],
        0,
    ),
    # The claimant's own £200 of ESA with £10,000 of capital: tariff income of
    # £832 a year leaves no award on the formula's reading, but the reform
    # pays the reported amount, before any screen.
    "own_esa_over_tariff": (
        [adult(**CARER, income_support_reported=1_000, esa_income_reported=200)],
        10_000,
    ),
    # Only an adult outside the couple reports Income Support.
    "excluded_income_support": (
        [
            adult(age=40, claimant_or_partner=True),
            adult(**NOT_IN_COUPLE, income_support_reported=1_000),
        ],
        0,
    ),
}
NAMES = list(FAMILIES)


def situation():
    people, benunits, households = {}, {}, {}
    for family, (members, capital) in FAMILIES.items():
        names = []
        for i, person in enumerate(members):
            name = f"{family}_{i}"
            people[name] = person
            names.append(name)
        benunits[family] = {
            "members": names,
            "income_support_assessable_capital": every_year(capital),
            "esa_income_assessable_capital": every_year(capital),
            "jsa_income_assessable_capital": every_year(capital),
        }
        households[family] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


def by_family(simulation, variable, year):
    return dict(zip(NAMES, simulation.calculate(variable, year).tolist()))


def by_person(simulation, variable, year):
    names = [
        f"{family}_{i}"
        for family, (members, _) in FAMILIES.items()
        for i in range(len(members))
    ]
    return dict(zip(names, simulation.calculate(variable, year).tolist()))


@pytest.fixture(scope="module")
def reformed():
    return Simulation(situation=situation(), scenario=REFORM)


def test_every_listed_benefit_has_what_the_reform_reads_and_sets():
    # The reform used to list Attendance Allowance, DLA and PIP, which have
    # no reported amount, and so raised before setting anything.
    variables = CountryTaxBenefitSystem().variables
    for benefit in BENEFITS:
        assert benefit in variables, benefit
        assert f"{benefit}_reported" in variables, benefit
    for name in [
        *PRE_MINIMUM.values(),
        *CLAIMANT_OR_PARTNER_AWARDS.values(),
        *CLAIMANT_OR_PARTNER_ONLY,
    ]:
        assert name in variables, name
    assert set(PRE_MINIMUM) <= set(BENEFITS)
    assert set(CLAIMANT_OR_PARTNER_AWARDS) <= set(BENEFITS)
    assert set(CLAIMANT_OR_PARTNER_ONLY) <= set(BENEFITS)


def test_the_reform_is_off_by_default():
    simulation = Simulation(situation=situation())
    for variable in ["esa_income", "claimant_or_partner_esa_income"]:
        assert simulation.get_holder(variable).get_known_periods() == []


def test_the_reform_sets_the_awards_for_ten_years(reformed):
    expected = list(range(DATASET_YEAR, DATASET_YEAR + YEARS_IN_FUTURE))
    for variable in [
        "esa_income",
        "jsa_income",
        "income_support",
        "claimant_or_partner_esa_income",
        "claimant_or_partner_jsa_income",
    ]:
        periods = reformed.get_holder(variable).get_known_periods()
        assert sorted(int(str(p)[:4]) for p in periods) == expected, variable


@pytest.mark.parametrize("year", YEARS)
def test_the_stored_awards_are_the_dataset_years_reports(reformed, year):
    # Every member's report, at its dataset-year amount in every year.
    assert by_family(reformed, "esa_income", year) == {
        "excluded_adult": 3_000,
        "excluded_adult_no_award": 3_000,
        "own_esa": 3_000,
        "own_jsa": 0,
        "own_esa_over_tariff": 200,
        "excluded_income_support": 0,
    }
    assert by_family(reformed, "jsa_income", year) == {
        "excluded_adult": 2_000,
        "excluded_adult_no_award": 2_000,
        "own_esa": 0,
        "own_jsa": 2_000,
        "own_esa_over_tariff": 0,
        "excluded_income_support": 0,
    }


@pytest.mark.parametrize("year", YEARS[1:])
def test_later_years_need_the_awards_set_explicitly(reformed, year):
    # In a later year the reports have been uprated, so the stored £3,000
    # equals neither their plain total nor the award on them. Read by value
    # alone, it would be the claimant's or partner's: the excluded adult's
    # ESA would become the couple's.
    reported_total = reformed.calculate("esa_income_reported", year, map_to="benunit")
    excluded = NAMES.index("excluded_adult")
    assert reported_total[excluded] > 3_000
    by_value_alone = claimant_or_partner_award(
        reformed.populations["benunit"],
        period(year),
        "esa_income",
        "esa_income_reported",
        income_related_esa_award,
    )
    assert by_value_alone[excluded] == 3_000


@pytest.mark.parametrize("year", YEARS)
def test_the_claimant_or_partner_awards_are_their_own_reports(reformed, year):
    assert by_family(reformed, "claimant_or_partner_esa_income", year) == {
        "excluded_adult": 0,
        "excluded_adult_no_award": 0,
        "own_esa": 3_000,
        "own_jsa": 0,
        "own_esa_over_tariff": 200,
        "excluded_income_support": 0,
    }
    assert by_family(reformed, "claimant_or_partner_jsa_income", year) == {
        "excluded_adult": 0,
        "excluded_adult_no_award": 0,
        "own_esa": 0,
        "own_jsa": 2_000,
        "own_esa_over_tariff": 0,
        "excluded_income_support": 0,
    }
    # Income Support is the claimant's family's award, from their own reports.
    assert by_family(reformed, "income_support", year) == {
        "excluded_adult": 1_000,
        "excluded_adult_no_award": 0,
        "own_esa": 1_000,
        "own_jsa": 1_000,
        "own_esa_over_tariff": 1_000,
        "excluded_income_support": 0,
    }


@pytest.mark.parametrize("year", YEARS)
def test_both_income_support_limbs_read_the_claimant_or_partner_awards(reformed, year):
    # The carer with an Income Support award is eligible beside an adult
    # outside the couple who reports ESA and JSA: neither limb bars the claim.
    # The same carer's own ESA bars it under s.124(1)(h), and their own JSA
    # under s.124(1)(f), every year. The reform pays the £200 of ESA the
    # tariff income would extinguish, so that bars it too.
    assert by_family(reformed, "income_support_eligible", year) == {
        "excluded_adult": True,
        "excluded_adult_no_award": False,
        "own_esa": False,
        "own_jsa": False,
        "own_esa_over_tariff": False,
        "excluded_income_support": False,
    }


@pytest.mark.parametrize("year", YEARS)
def test_the_council_tax_reduction_passport(reformed, year):
    # The working-age schemes passport an applicant or partner on Income
    # Support, income-based JSA or income-related ESA (SI 2012/2886 Sch,
    # para 33(2)). Another member's award passports nobody else.
    assert by_family(
        reformed, "council_tax_reduction_relevant_income_based_benefit", year
    ) == {
        "excluded_adult": True,
        "excluded_adult_no_award": False,
        "own_esa": True,
        "own_jsa": True,
        "own_esa_over_tariff": True,
        "excluded_income_support": False,
    }


@pytest.mark.parametrize("year", YEARS)
def test_each_person_is_on_their_own_award(reformed, year):
    on_esa = by_person(reformed, "is_on_income_related_esa", year)
    on_jsa = by_person(reformed, "is_on_income_based_jsa", year)
    assert not on_esa["excluded_adult_no_award_0"]
    assert on_esa["excluded_adult_no_award_1"]
    assert not on_jsa["excluded_adult_no_award_0"]
    assert on_jsa["excluded_adult_no_award_1"]
    assert on_esa["own_esa_0"] and not on_jsa["own_esa_0"]
    assert on_jsa["own_jsa_0"] and not on_esa["own_jsa_0"]


def test_a_multi_year_dataset_uses_its_first_year():
    # A situation's dataset stores its year as text and a multi-year dataset
    # as a number; both start the reform's ten years. Here the second year's
    # reports differ, but the reform reads the first year's.
    def year(fiscal_year, esa):
        person = pd.DataFrame(
            {
                "person_id": [1, 2, 3],
                "person_benunit_id": [1, 1, 2],
                "person_household_id": [1, 1, 2],
                "age": [40, 30, 40],
                "is_claimant_or_partner": [True, False, True],
                "esa_income_reported": esa,
            }
        )
        return UKSingleYearDataset(
            person=person,
            benunit=pd.DataFrame({"benunit_id": [1, 2]}),
            household=pd.DataFrame({"household_id": [1, 2]}),
            fiscal_year=fiscal_year,
        )

    dataset = UKMultiYearDataset(
        datasets=[
            year(DATASET_YEAR, [0.0, 3_000.0, 3_000.0]),
            year(DATASET_YEAR + 1, [0.0, 3_100.0, 3_100.0]),
        ]
    )
    simulation = Simulation(dataset=dataset, scenario=REFORM)
    for year_ in YEARS:
        assert simulation.calculate("esa_income", year_).tolist() == [3_000, 3_000]
        assert simulation.calculate(
            "claimant_or_partner_esa_income", year_
        ).tolist() == [0, 3_000]


REPORTED = ["esa_income_reported", "jsa_income_reported", "income_support_reported"]


@st.composite
def reporting_families(draw):
    """One to three adults, the first one or two the claimant and partner,
    each reporting ESA, JSA and Income Support in the dataset year."""
    amounts = st.sampled_from([0, 0, 200, 3_000, 65_536.01])
    n_couple = draw(st.integers(1, 2))
    n_others = draw(st.integers(0, 2))
    members = []
    for i in range(n_couple + n_others):
        members.append(
            {
                "age": every_year(40 - i),
                "is_claimant_or_partner": every_year(i < n_couple),
                "receives_carer_benefit": every_year(draw(st.booleans())),
                "current_education": every_year("NOT_IN_EDUCATION"),
                **{name: {DATASET_YEAR: draw(amounts)} for name in REPORTED},
            }
        )
    return members, draw(st.sampled_from([0, 10_000, 20_000]))


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.lists(reporting_families(), min_size=1, max_size=8))
def test_the_reform_splits_every_familys_reports_between_the_awards(drawn):
    people, benunits, households = {}, {}, {}
    for i, (members, capital) in enumerate(drawn):
        names = [f"p{i}_{j}" for j in range(len(members))]
        people.update(zip(names, members))
        benunits[f"b{i}"] = {
            "members": names,
            "income_support_assessable_capital": every_year(capital),
            "esa_income_assessable_capital": every_year(capital),
            "jsa_income_assessable_capital": every_year(capital),
        }
        households[f"h{i}"] = {"members": names}
    simulation = Simulation(
        situation={"people": people, "benunits": benunits, "households": households},
        scenario=REFORM,
    )

    def total(name, couple_only):
        return np.array(
            [
                sum(
                    member[name][DATASET_YEAR]
                    for member in members
                    if member["is_claimant_or_partner"][DATASET_YEAR] or not couple_only
                )
                for members, _ in drawn
            ],
            dtype=np.float32,
        )

    for year in YEARS:
        for award, scoped in CLAIMANT_OR_PARTNER_AWARDS.items():
            stored = simulation.calculate(award, year)
            couple = simulation.calculate(scoped, year)
            # Conservation: the stored award is everyone's dataset-year
            # reports, and the couple's part is their own.
            np.testing.assert_allclose(
                stored, total(f"{award}_reported", False), rtol=1e-6
            )
            np.testing.assert_allclose(
                couple, total(f"{award}_reported", True), rtol=1e-6
            )
            assert ((couple >= 0) & (couple <= stored)).all()
        np.testing.assert_allclose(
            simulation.calculate("income_support", year),
            total("income_support_reported", True),
            rtol=1e-6,
        )
        # Either income-related award of the couple bars Income Support, and
        # the passport follows the couple's awards alone.
        esa = simulation.calculate("claimant_or_partner_esa_income", year) > 0
        jsa = simulation.calculate("claimant_or_partner_jsa_income", year) > 0
        income_support = simulation.calculate("income_support", year) > 0
        eligible = simulation.calculate("income_support_eligible", year)
        assert not (eligible & (esa | jsa)).any()
        np.testing.assert_array_equal(
            simulation.calculate(
                "council_tax_reduction_relevant_income_based_benefit", year
            ),
            esa | jsa | income_support,
        )
