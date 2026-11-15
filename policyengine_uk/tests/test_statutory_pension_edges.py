"""Synthetic regressions for FA 2004 ss. 188, 190, 228ZA and 233.

The NICs-only salary-sacrifice cap must preserve annual-allowance inputs,
including after age 75 and at the basic RAS relief boundary. Charge
comparisons either keep ordinary tax bands stable or hold ordinary tax
inputs fixed; unrestricted charge invariance is not asserted.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, Phase, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def make_sim(year, **values):
    s = Simulation(
        situation={
            "people": {"p": {k: {year: v} for k, v in values.items()}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )
    s.apply_parameter_changes(
        {
            "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate": {
                str(year): 0
            }
        }
    )
    return s


@pytest.mark.parametrize("year", [2029, 2030])
@pytest.mark.parametrize("scheme", ["DC", "DB"])
def test_nics_cap_does_not_create_taper_after_age75(year, scheme):
    values = dict(
        age=80,
        employment_income_before_lsr=160000,
        pension_contributions_via_salary_sacrifice=30000,
        employer_pension_contributions=100000,
    )
    if scheme == "DB":
        values["pension_contributions_for_annual_allowance"] = 150000
    s = make_sim(year, **values)
    actual = {
        v: float(s.calculate(v, year)[0])
        for v in [
            "pension_contributions_for_annual_allowance",
            "pension_annual_allowance_threshold_income",
            "pension_annual_allowance_adjusted_income",
            "pension_annual_allowance",
            "personal_pension_contributions_tax",
        ]
    }
    # The full 30,000 sacrifice raises 160,000 cash pay to threshold 190,000.
    # The 28,000 returned for NICs remains employer pension provision in law.
    assert actual["pension_annual_allowance_threshold_income"] == 190000
    assert actual["pension_annual_allowance"] == 60000
    assert actual["personal_pension_contributions_tax"] == (
        31500 if scheme == "DC" else 40500
    )


def test_post75_dc_member_contributions_are_excluded_from_input_amount():
    s = make_sim(
        2024,
        age=80,
        private_pension_income=210000,
        personal_pension_contributions=50000,
        employer_pension_contributions=80000,
    )
    actual = {
        v: float(s.calculate(v, 2024)[0])
        for v in [
            "pension_contributions_for_annual_allowance",
            "pension_annual_allowance_threshold_income",
            "pension_annual_allowance_adjusted_income",
            "pension_annual_allowance",
            "personal_pension_contributions_tax",
        ]
    }
    assert actual["pension_contributions_for_annual_allowance"] == 80000
    assert actual["pension_annual_allowance_threshold_income"] == 210000
    assert actual["pension_annual_allowance_adjusted_income"] == 240000
    assert actual["pension_annual_allowance"] == 60000
    assert actual["personal_pension_contributions_tax"] == 9000


AA_VARIABLES = [
    "pension_contributions_for_annual_allowance",
    "pension_annual_allowance_threshold_income",
    "pension_annual_allowance_adjusted_income",
    "pension_annual_allowance",
]


def _population_simulation(people, year, cap=2_000):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, values in enumerate(people):
        name = f"p{index}"
        situation["people"][name] = {
            key: {year: value} for key, value in values.items()
        }
        situation["benunits"][f"b{index}"] = {"members": [name]}
        situation["households"][f"h{index}"] = {"members": [name]}
    sim = Simulation(situation=situation)
    sim.apply_parameter_changes(
        {
            "gov.hmrc.national_insurance.salary_sacrifice_pension_cap": {
                str(year): cap
            },
            "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate": {
                str(year): 0
            },
        }
    )
    return sim


@pytest.mark.parametrize("year", [2029, 2030])
def test_nics_cap_preserves_basic_ras_threshold_income_boundary(year):
    """Sections 190(2)-(4) and 191(7) preserve the full basic RAS amount."""
    values = {
        "age": 45,
        "employment_income_before_lsr": 2_000,
        "pension_contributions_via_salary_sacrifice": 201_000,
        "employer_pension_contributions": 100_000,
        "personal_pension_contributions": 3_600,
    }
    for cap in [2_000, float("inf")]:
        sim = _population_simulation([values], year, cap)
        # Cash pay plus full sacrifice less the full basic RAS relief.
        expected = {
            "pension_contributions_for_annual_allowance": 304_600,
            "pension_annual_allowance_threshold_income": 199_400,
            "pension_annual_allowance_adjusted_income": 303_000,
            "pension_annual_allowance": 60_000,
        }
        for variable, amount in expected.items():
            assert float(sim.calculate(variable, year)[0]) == amount, (cap, variable)


@pytest.mark.parametrize("year", [2026, 2029, 2030])
@pytest.mark.parametrize("cap", [2_000, float("inf")], ids=["capped", "uncapped"])
@pytest.mark.parametrize("net_pay", [2_000, 3_600], ids=["earnings", "above_earnings"])
def test_basic_ras_uplift_does_not_relieve_net_pay_in_aa_loss_cap(year, cap, net_pay):
    """FA 2004 ss.190(3)/191(7) reserve above-earnings basic relief for RAS."""
    sim = _population_simulation(
        [
            {
                "age": 45,
                "employment_income_before_lsr": 2_000,
                "employee_pension_contributions_reported": net_pay,
                "personal_pension_contributions": 0,
                "dividend_income": 250_000,
                "trading_loss": 200_000,
                "employer_pension_contributions": 100_000,
                "pension_contributions_via_salary_sacrifice": 12_500,
            }
        ],
        year,
        cap,
    )
    # Only 2,000 net pay is relievable. ATI is 250,000, so the 25% loss
    # cap is 62,500 and statutory net income is 187,500. The 12,500
    # sacrifice brings threshold income exactly to the untapered boundary.
    expected = {
        "pension_annual_allowance_threshold_income": 200_000,
        "pension_annual_allowance_adjusted_income": 302_000,
        "pension_contributions_for_annual_allowance": 112_500 + net_pay,
        "pension_annual_allowance": 60_000,
        "personal_pension_contributions_tax": (52_500 + net_pay) * 0.45,
    }
    for variable, amount in expected.items():
        assert float(sim.calculate(variable, year)[0]) == pytest.approx(
            amount, abs=0.01
        )


@pytest.mark.parametrize("year", [2029, 2030])
@pytest.mark.parametrize("scheme", ["DC", "DB"])
@pytest.mark.parametrize("method", ["net_pay", "RAS"])
@pytest.mark.parametrize("age", [45, 80])
def test_nics_cap_preserves_aa_across_scheme_method_and_age(year, scheme, method, age):
    """The review's 16 cases retain the same top rate on the whole excess.

    This charge comparison has stable ordinary tax bands: both cash pay and
    pay after net-pay relief exceed the additional-rate threshold at either
    cap setting. General charge invariance would be false because the cap's
    separate ordinary-income/ANI behavior can change the personal allowance.
    """
    values = {
        "age": age,
        "employment_income_before_lsr": 160_000,
        "pension_contributions_via_salary_sacrifice": 30_000,
        "employer_pension_contributions": 100_000,
        (
            "employee_pension_contributions_reported"
            if method == "net_pay"
            else "personal_pension_contributions"
        ): 10_000,
    }
    if scheme == "DB":
        values["pension_contributions_for_annual_allowance"] = 150_000
    pension_input = 150_000 if scheme == "DB" else (140_000 if age < 75 else 130_000)
    expected = {
        "pension_contributions_for_annual_allowance": pension_input,
        "pension_annual_allowance_threshold_income": 180_000 if age < 75 else 190_000,
        # All own member contributions remain deductible from adjusted income,
        # including the post-75 contributions excluded from the DC input.
        "pension_annual_allowance_adjusted_income": 160_000 + pension_input - 10_000,
        "pension_annual_allowance": 60_000,
        "personal_pension_contributions_tax": (pension_input - 60_000) * 0.45,
    }
    for cap in [2_000, float("inf")]:
        sim = _population_simulation([values], year, cap)
        for variable, amount in expected.items():
            assert float(sim.calculate(variable, year)[0]) == pytest.approx(
                amount, abs=0.01
            ), (cap, variable)


@st.composite
def _pension_person(draw, scheme):
    method = draw(st.sampled_from(["net_pay", "RAS"]))
    values = {
        "age": draw(st.sampled_from([45, 74, 75, 80, 90])),
        "employment_income_before_lsr": draw(
            st.one_of(st.integers(0, 3_600), st.integers(3_601, 400_000))
        ),
        "pension_contributions_via_salary_sacrifice": draw(st.integers(0, 300_000)),
        "employer_pension_contributions": draw(st.integers(0, 200_000)),
        (
            "employee_pension_contributions_reported"
            if method == "net_pay"
            else "personal_pension_contributions"
        ): draw(st.integers(0, 100_000)),
    }
    if scheme == "DB":
        values["pension_contributions_for_annual_allowance"] = draw(
            st.integers(0, 400_000)
        )
    return values


def _assert_pension_input_path(sim, year, scheme):
    """Partial person inputs would bypass the default DC formula for everyone."""
    periods = sim.get_holder(
        "pension_contributions_for_annual_allowance"
    ).get_input_periods("default")
    assert [str(period) for period in periods] == (
        [str(year)] if scheme == "DB" else []
    )


def _assert_ani_input_path(sim, year, supplied_ani):
    """ANI inputs override the whole person array, including partial inputs."""
    periods = sim.get_holder("adjusted_net_income").get_input_periods("default")
    assert [str(period) for period in periods] == ([str(year)] if supplied_ani else [])


def _charges_with_fixed_ordinary_tax_inputs(result_sets, year):
    """Test the AA inputs to the charge separately from ordinary income tax.

    A fixed additional-rate base, no RAS and no allowances keep the charge
    independent of the cap's separate effects on ANI/personal allowances.
    The taper incomes and pension input above are always calculated from
    the original pay/contribution inputs, without these overrides.

    One simulation holds the people of every result set. Each person has
    their own benefit unit and household and supplies the same inputs as
    every other, so no person's charge reads another's. Returns each result
    set's charges.
    """
    people = [
        {
            "age": 45,
            "net_income": 400_000,
            "allowances": 0,
            "personal_pension_contributions": 0,
            "pension_contributions_relief": 0,
            "pension_contributions_for_annual_allowance": float(pension_input),
            "pension_annual_allowance": float(allowance),
        }
        for results in result_sets
        for pension_input, allowance in zip(
            results["pension_contributions_for_annual_allowance"],
            results["pension_annual_allowance"],
        )
    ]
    sim = _population_simulation(people, year)
    charge = np.asarray(sim.calculate("personal_pension_contributions_tax", year))
    sizes = [len(results["pension_annual_allowance"]) for results in result_sets]
    charges = np.split(charge, np.cumsum(sizes)[:-1])
    for results, set_charge in zip(result_sets, charges):
        excess = np.maximum(
            0,
            results["pension_contributions_for_annual_allowance"]
            - results["pension_annual_allowance"],
        )
        np.testing.assert_allclose(set_charge, excess * 0.45, rtol=0, atol=0.05)
    return charges


def _aa_results_under_both_caps(people, year, scheme, supplied_ani):
    """The AA variables with the NICs cap at 2,000 and with no cap."""
    results = []
    for cap in [2_000, float("inf")]:
        sim = _population_simulation(people, year, cap)
        _assert_pension_input_path(sim, year, scheme)
        _assert_ani_input_path(sim, year, supplied_ani)
        results.append(
            {
                variable: np.asarray(sim.calculate(variable, year))
                for variable in AA_VARIABLES
            }
        )
    return results


def _assert_caps_agree(groups, year):
    """Each group's AA variables and charge agree under both cap settings.

    ``groups`` maps a label to the results ``_aa_results_under_both_caps``
    returns. One charge simulation serves every group and both caps.
    """
    for label, results in groups.items():
        for variable in AA_VARIABLES:
            np.testing.assert_allclose(
                results[0][variable],
                results[1][variable],
                rtol=0,
                atol=0.05,
                err_msg=f"{label}: {variable}",
            )
    result_sets = [results[cap] for results in groups.values() for cap in (0, 1)]
    charges = _charges_with_fixed_ordinary_tax_inputs(result_sets, year)
    for index, label in enumerate(groups):
        np.testing.assert_allclose(
            charges[2 * index],
            charges[2 * index + 1],
            rtol=0,
            atol=0.05,
            err_msg=f"{label}: personal_pension_contributions_tax",
        )


@pytest.mark.parametrize("year", [2029, 2030])
@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    dc_people=st.lists(_pension_person("DC"), min_size=4, max_size=10),
    db_people=st.lists(_pension_person("DB"), min_size=4, max_size=10),
)
def test_nics_cap_preserves_aa_inputs_and_charge_with_fixed_ordinary_tax(
    dc_people, db_people, year
):
    """All ages/earnings preserve AA computations when the NICs cap varies.

    The charge comparison fixes ordinary tax inputs. It makes no unrestricted
    claim about the charge, ANI, personal allowances or ordinary income tax.
    ``test_nics_cap_preserves_aa_inputs_and_charge_with_supplied_ani`` tests
    the fixed populations with a supplied ANI.
    """
    # Keep every default DC record, including the fixed witnesses, separate
    # from supplied DB inputs, which otherwise zero the DC input array.
    dc_people = [
        {
            "age": 80,
            "employment_income_before_lsr": 160_000,
            "pension_contributions_via_salary_sacrifice": 30_000,
            "employer_pension_contributions": 100_000,
        },
        {
            "age": 45,
            "employment_income_before_lsr": 2_000,
            "pension_contributions_via_salary_sacrifice": 201_000,
            "employer_pension_contributions": 100_000,
            "personal_pension_contributions": 3_600,
        },
    ] + dc_people
    groups = {
        "DC": _aa_results_under_both_caps(dc_people, year, "DC", False),
        "DB": _aa_results_under_both_caps(db_people, year, "DB", False),
    }
    for results in groups["DC"]:
        np.testing.assert_array_equal(
            results["pension_contributions_for_annual_allowance"][:2],
            [130_000, 304_600],
        )
    _assert_caps_agree(groups, year)


@pytest.mark.parametrize("year", [2029, 2030])
def test_nics_cap_preserves_aa_inputs_and_charge_with_supplied_ani(year):
    """Supplied ANI fixes threshold income whatever the NICs cap.

    These populations depend on no drawn value, so this test runs them once
    for each year.
    """
    # ANI is a partial-input override, so each person in these separate
    # simulations must supply it. Loss relief is already reflected in ANI;
    # neither actual nor synthetic pay/loss relief can reconstruct it again.
    ani_people = [
        {
            "age": age,
            "employment_income_before_lsr": 2_000,
            "pension_contributions_via_salary_sacrifice": 201_000,
            "employer_pension_contributions": 100_000,
            "adjusted_net_income": 150_000,
            "trading_loss": loss,
            **contributions,
        }
        for age in [45, 80]
        for loss in [0, 10_000]
        for contributions in [
            {},
            {"gift_aid": 800, "employee_pension_contributions_reported": 4_000},
            {"gift_aid": 800, "personal_pension_contributions": 4_000},
        ]
    ]
    ani_db_people = [
        {**person, "pension_contributions_for_annual_allowance": 350_000}
        for person in ani_people
    ]
    groups = {
        "DC with ANI": _aa_results_under_both_caps(ani_people, year, "DC", True),
        "DB with ANI": _aa_results_under_both_caps(ani_db_people, year, "DB", True),
    }
    # Gross Gift Aid is 1,000. At age 45 actual earnings allow 2,000 net-pay
    # relief or 3,600 RAS relief; age 80 allows neither. The loss never
    # changes an already supplied ANI.
    expected_adjusted = {
        "DC with ANI": [451_000, 454_000, 455_600] * 2
        + [451_000, 448_000, 448_000] * 2,
        "DB with ANI": [500_000, 499_000, 500_600] * 2
        + [500_000, 497_000, 497_000] * 2,
    }
    for label, both_caps in groups.items():
        for results in both_caps:
            np.testing.assert_array_equal(
                results["pension_annual_allowance_threshold_income"],
                [351_000, 352_000, 352_000] * 4,
            )
            np.testing.assert_array_equal(
                results["pension_annual_allowance_adjusted_income"],
                expected_adjusted[label],
            )
            np.testing.assert_array_equal(
                results["pension_annual_allowance"],
                np.full(len(ani_people), 10_000),
            )
    _assert_caps_agree(groups, year)


@pytest.mark.parametrize("year", [2029, 2030])
@pytest.mark.parametrize("scheme", ["DC", "DB"])
@settings(
    max_examples=3,
    database=None,
    deadline=None,
    phases=[Phase.explicit, Phase.generate],
)
@example(loss=10_000)
@given(loss=st.integers(min_value=0, max_value=50_000))
def test_trade_losses_do_not_leak_nics_reclassification_into_aa(year, scheme, loss):
    """Income-dependent Step 2 relief uses actual income for both AA tests."""
    people = []
    for age in [45, 74, 75, 80]:
        for method in ["net_pay", "RAS"]:
            values = {
                "age": age,
                "employment_income_before_lsr": 2_000,
                "pension_contributions_via_salary_sacrifice": 201_000,
                "employer_pension_contributions": 100_000,
                "trading_loss": loss,
                (
                    "employee_pension_contributions_reported"
                    if method == "net_pay"
                    else "personal_pension_contributions"
                ): 600,
            }
            if scheme == "DB":
                values["pension_contributions_for_annual_allowance"] = 350_000
            people.append(values)
    results = []
    for cap in [2_000, float("inf")]:
        sim = _population_simulation(people, year, cap)
        _assert_pension_input_path(sim, year, scheme)
        results.append(
            {
                variable: np.asarray(sim.calculate(variable, year))
                for variable in AA_VARIABLES
            }
        )
    for variable in AA_VARIABLES:
        np.testing.assert_array_equal(
            results[0][variable],
            results[1][variable],
            err_msg=f"{year=} {scheme=} {loss=} {variable=}",
        )
