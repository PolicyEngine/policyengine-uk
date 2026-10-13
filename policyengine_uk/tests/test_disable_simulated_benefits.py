"""disable_simulated_benefits pays each family the benefits it reported.

The reform (gov.contrib.policyengine.disable_simulated_benefits) sets each
listed benefit, in the dataset year and the nine years after it, to the
amount reported in the dataset year. esa_income_reported and
jsa_income_reported are uprated, so in a later year a stored esa_income or
jsa_income equals neither the award on that year's reports nor their plain
total. Read by value alone, it would then
be taken to be wholly the claimant's or partner's, another member's award
included. So the reform also sets the claimant's and partner's awards
(claimant_or_partner_esa_income, claimant_or_partner_jsa_income) for each
year, from the dataset-year reports of whoever is the claimant or partner
that year, and Income Support from theirs alone. Both of Income Support's income-related limbs (SSCBA 1992
s.124(1)(f) and (h)) and the council tax reduction passport read those
awards.

Each family below is its own benefit unit and household. Reported amounts are
entered for the dataset year only, so later years uprate them. Everything
else is entered for every year.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import period

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.model_api import Reform
from policyengine_uk.reforms.policyengine.disable_simulated_benefits import (
    BENEFITS,
    CLAIMANT_OR_PARTNER_AWARDS,
    CLAIMANT_OR_PARTNER_ONLY,
    NOT_MOVED,
    PRE_MINIMUM,
    YEARS_IN_FUTURE,
    disable_simulated_benefits,
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


@pytest.fixture(scope="module")
def unreformed():
    return Simulation(situation=situation())


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
        *NOT_MOVED,
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
def test_no_family_is_moved_off_its_legacy_benefits(reformed, unreformed, year):
    # Income-based JSA and Income Support close from April 2026, and the
    # model then moves a working-age family reporting either, unless it is on
    # Pension Credit, off all its legacy benefits (legacy_benefits_closed), so
    # their awards end. Every family here reports one of them. The reform pays every reported award in every
    # year, so it holds the move off; otherwise an adult outside the couple
    # would stop being on the ESA and JSA the reform still pays them
    # (test_each_person_is_on_their_own_award).
    moved = year > DATASET_YEAR
    assert by_family(unreformed, "legacy_benefits_closed", year) == dict.fromkeys(
        NAMES, moved
    )
    assert by_family(reformed, "legacy_benefits_closed", year) == dict.fromkeys(
        NAMES, False
    )
    ten_years = list(range(DATASET_YEAR, DATASET_YEAR + YEARS_IN_FUTURE))
    for variable in NOT_MOVED:
        assert known_years(reformed, variable) == ten_years, variable


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
    # reports differ, but the reform reads the first year's. The second
    # member is 18 and the first 40, so after the data's two years the
    # model's presumption reads them as the claimant's child, as the data
    # does, and the roles are the same in every year.
    def year(fiscal_year, esa):
        person = pd.DataFrame(
            {
                "person_id": [1, 2, 3],
                "person_benunit_id": [1, 1, 2],
                "person_household_id": [1, 1, 2],
                "age": [40, 18, 40],
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
        roles = simulation.calculate("is_claimant_or_partner", year_)
        assert roles.tolist() == [True, False, True]
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


# The reform class itself, as create_structural_reforms_from_parameters builds
# it when the parameter is on.
ON = SimpleNamespace(
    gov=SimpleNamespace(
        contrib=SimpleNamespace(
            policyengine=SimpleNamespace(disable_simulated_benefits=True)
        )
    )
)
DisableSimulatedBenefits = disable_simulated_benefits(lambda _: ON, None)
SET_BY_THE_REFORM = [
    "esa_income",
    "claimant_or_partner_esa_income",
    "claimant_or_partner_jsa_income",
    "income_support",
]


def known_years(simulation, variable):
    holder = simulation.get_holder(variable)
    return sorted(int(str(p)[:4]) for p in holder.get_known_periods())


def test_a_clone_or_branch_applies_the_reform_to_itself_alone(unreformed):
    # A clone's copy of the tax-benefit system links to the clone, and a
    # branch shares its parent's system. The reform reaches the simulation
    # through that link, so it must reach the clone or branch applying it,
    # never the parent.
    parent = Simulation(situation=situation())
    clone = parent.clone()
    assert clone.tax_benefit_system.simulation is clone
    clone.apply_reform(DisableSimulatedBenefits)
    branch = parent.get_branch("reformed")
    assert branch.tax_benefit_system is parent.tax_benefit_system
    branch.apply_reform(DisableSimulatedBenefits)
    assert parent.tax_benefit_system.simulation is parent
    ten_years = list(range(DATASET_YEAR, DATASET_YEAR + YEARS_IN_FUTURE))
    for variable in SET_BY_THE_REFORM:
        assert known_years(parent, variable) == [], variable
        assert known_years(clone, variable) == ten_years, variable
    excluded = NAMES.index("excluded_adult")
    for year in YEARS:
        for simulation in (clone, branch):
            assert simulation.calculate("esa_income", year)[excluded] == 3_000
            assert (
                simulation.calculate("claimant_or_partner_esa_income", year)[excluded]
                == 0
            )
        # The parent still simulates ESA, as a simulation without the reform
        # does: the excluded adult's report in the dataset year, and nothing
        # once the closure of income-based JSA and Income Support has moved
        # the family off its legacy benefits.
        np.testing.assert_array_equal(
            parent.calculate("esa_income", year),
            unreformed.calculate("esa_income", year),
        )
    assert parent.calculate("esa_income", DATASET_YEAR)[excluded] == 3_000


# Applied after the simulation is built: passed as reform=, or applied to a
# clone or a branch.
LATER = ["reform=", "clone", "branch"]


@pytest.mark.parametrize("route", LATER)
def test_a_reform_applied_later_keeps_what_it_sets_through_a_reset(route):
    # input_variables is taken when a simulation is built, and
    # reset_calculations deletes every other variable's values (as
    # derivative did before policyengine-core 3.33.0).
    # A reform applied later names what it sets, or a reset deletes the
    # claimant-or-partner awards and recalculates them. esa_income is entered
    # here too, so a reset kept it while deleting its claimant-or-partner
    # part, and the formula then read the excluded adult's ESA as the couple's.
    entered = situation()
    for benunit in entered["benunits"].values():
        benunit["esa_income"] = {DATASET_YEAR: 3_000}
    if route == "reform=":
        parent = None
        simulation = Simulation(situation=entered, reform=DisableSimulatedBenefits)
    else:
        parent = Simulation(situation=entered)
        names = parent.input_variables
        recorded = list(names)
        simulation = (
            parent.clone() if route == "clone" else parent.get_branch("reformed")
        )
        simulation.apply_reform(DisableSimulatedBenefits)
        # A clone or branch shares its parent's list until it names more.
        assert parent.input_variables is names
        assert parent.input_variables == recorded
        assert "claimant_or_partner_esa_income" not in recorded
    set_by_the_reform = [
        *BENEFITS,
        *PRE_MINIMUM.values(),
        *CLAIMANT_OR_PARTNER_AWARDS.values(),
        *NOT_MOVED,
    ]
    for variable in set_by_the_reform:
        assert variable in simulation.input_variables, variable
    excluded = NAMES.index("excluded_adult")
    year = YEARS[1]
    before = {
        variable: simulation.calculate(variable, year)
        for variable in [*set_by_the_reform, "income_support_eligible"]
    }
    assert before["claimant_or_partner_esa_income"][excluded] == 0
    assert before["income_support_eligible"][excluded]
    # derivative recalculates on a clone: before policyengine-core 3.33.0
    # after the same deletions, and from 3.33.0 keeping every input.
    assert not simulation.derivative(
        "claimant_or_partner_esa_income", "employment_income", year
    ).any()
    simulation.reset_calculations()
    for variable, value in before.items():
        np.testing.assert_array_equal(
            simulation.calculate(variable, year), value, err_msg=variable
        )


@pytest.mark.parametrize("route", ["itself", "clone", "branch"])
def test_a_reform_that_replaces_inputs_set_after_the_build_keeps_them(route):
    # Inputs set after the build are recorded as inputs, but input_variables
    # does not name them. A reform applied to the same simulation, or to a
    # clone, that replaces one adds no new record, so the reform's inputs are
    # named by what it sets. A branch stores its inputs under its own name,
    # so there every record is new.
    entered = situation()
    for benunit in entered["benunits"].values():
        benunit["esa_income"] = {DATASET_YEAR: 3_000}
    parent = Simulation(situation=entered)
    for year in range(DATASET_YEAR, DATASET_YEAR + YEARS_IN_FUTURE):
        parent.set_input(
            "claimant_or_partner_esa_income", year, np.full(len(NAMES), 100)
        )
    # Set after the build and not by the reform, so the reform does not name it.
    parent.set_input(
        "housing_benefit_applicable_income", YEARS[1], np.zeros(len(NAMES))
    )
    names = parent.input_variables
    recorded = list(names)
    assert "claimant_or_partner_esa_income" not in recorded
    if route == "itself":
        simulation = parent
    elif route == "clone":
        simulation = parent.clone()
    else:
        simulation = parent.get_branch("reformed")
    simulation.apply_reform(DisableSimulatedBenefits)
    if route != "itself":
        assert parent.input_variables is names
        assert parent.input_variables == recorded
    for variable in SET_BY_THE_REFORM:
        assert variable in simulation.input_variables, variable
    assert "housing_benefit_applicable_income" not in simulation.input_variables
    excluded = NAMES.index("excluded_adult")
    year = YEARS[1]
    before = {
        variable: simulation.calculate(variable, year)
        for variable in [*SET_BY_THE_REFORM, "income_support_eligible"]
    }
    assert before["claimant_or_partner_esa_income"][excluded] == 0
    assert before["income_support_eligible"][excluded]
    assert not simulation.derivative(
        "claimant_or_partner_esa_income", "employment_income", year
    ).any()
    simulation.reset_calculations()
    for variable, value in before.items():
        np.testing.assert_array_equal(
            simulation.calculate(variable, year), value, err_msg=variable
        )


class RemoveIncomeRelatedAwards(Reform):
    def apply(self):
        self.neutralize_variable("esa_income")
        self.neutralize_variable("jsa_income")


def test_neutralizing_an_award_removes_the_claimant_or_partners_award():
    # The claimant's and partner's award is part of esa_income or
    # jsa_income: a reform that removes the award removes their part too,
    # including the part the reform set as an input.
    simulation = Simulation(situation=situation(), scenario=REFORM)
    simulation.apply_reform(RemoveIncomeRelatedAwards)
    for year in YEARS:
        for variable in [
            "esa_income",
            "jsa_income",
            "claimant_or_partner_esa_income",
            "claimant_or_partner_jsa_income",
        ]:
            assert simulation.calculate(variable, year).tolist() == [0] * len(NAMES), (
                variable,
                year,
            )
        # Without the income-related awards nothing bars Income Support, and
        # only Income Support passports council tax reduction.
        assert by_family(simulation, "income_support_eligible", year) == {
            "excluded_adult": True,
            "excluded_adult_no_award": False,
            "own_esa": True,
            "own_jsa": True,
            "own_esa_over_tariff": True,
            "excluded_income_support": False,
        }
        assert by_family(
            simulation, "council_tax_reduction_relevant_income_based_benefit", year
        ) == dict(
            zip(NAMES, (simulation.calculate("income_support", year) > 0).tolist())
        )
        assert not simulation.calculate("is_on_income_related_esa", year).any()
        assert not simulation.calculate("is_on_income_based_jsa", year).any()


def test_an_award_neutralized_first_is_not_set():
    # Neutralized before the reform runs: neither the award nor the
    # claimant's and partner's part of it takes what the reform sets.
    def remove(simulation):
        simulation.tax_benefit_system.neutralize_variable("esa_income")

    scenario = Scenario(
        applied_before_data_load=True,
        parameter_changes=REFORM.parameter_changes,
        simulation_modifier=remove,
    )
    simulation = Simulation(situation=situation(), scenario=scenario)
    assert known_years(simulation, "esa_income") == []
    assert known_years(simulation, "claimant_or_partner_esa_income") == []
    assert len(known_years(simulation, "claimant_or_partner_jsa_income")) == (
        YEARS_IN_FUTURE
    )
    for year in YEARS:
        assert not simulation.calculate("claimant_or_partner_esa_income", year).any()
        assert (
            by_family(simulation, "claimant_or_partner_jsa_income", year)["own_jsa"]
            == 2_000
        )


def test_neutralizing_an_award_removes_an_entered_claimant_or_partner_award():
    # The same without the reform, for an award entered directly.
    simulation = Simulation(situation=situation())
    simulation.set_input(
        "claimant_or_partner_esa_income", DATASET_YEAR, np.full(len(NAMES), 3_000)
    )
    assert simulation.calculate("claimant_or_partner_esa_income", DATASET_YEAR).all()
    simulation.apply_reform(RemoveIncomeRelatedAwards)
    assert not simulation.calculate(
        "claimant_or_partner_esa_income", DATASET_YEAR
    ).any()


@pytest.mark.parametrize("year", YEARS)
def test_another_members_income_support_is_never_the_familys(reformed, year):
    # The model pays Income Support only to the claimant's family, so
    # another member's own report is left out of income_support (and so of
    # household income) with the reform off, as the reform leaves it out.
    for simulation in (Simulation(situation=situation()), reformed):
        income_support = by_family(simulation, "income_support", year)
        assert income_support["excluded_income_support"] == 0


def test_the_claimant_and_partner_are_taken_in_each_year():
    # The amounts are held at the dataset year, but who the claimant and
    # partner are is read in each year, as every reader of the awards reads
    # it. Here the claimant in the dataset year is someone else's
    # non-dependant afterwards, and the other adult claims instead.
    first, later = DATASET_YEAR, YEARS[1:]

    def member(age, claimant_or_partner_in_first_year, **reported):
        person = adult(age, claimant_or_partner_in_first_year, **reported)
        person["is_claimant_or_partner"] = {
            first: claimant_or_partner_in_first_year,
            **{year: not claimant_or_partner_in_first_year for year in later},
        }
        return person

    people = {
        "a": member(40, True, esa_income_reported=3_000, income_support_reported=1_000),
        "b": member(35, False, esa_income_reported=1_000),
    }
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {"family": {"members": ["a", "b"]}},
            "households": {"home": {"members": ["a", "b"]}},
        },
        scenario=REFORM,
    )
    expected = {first: (3_000, 1_000)}
    expected.update({year: (1_000, 0) for year in later})
    for year, (claimant_or_partner_esa, income_support) in expected.items():
        assert simulation.calculate("esa_income", year)[0] == 4_000
        assert (
            simulation.calculate("claimant_or_partner_esa_income", year)[0]
            == claimant_or_partner_esa
        )
        assert simulation.calculate("income_support", year)[0] == income_support
