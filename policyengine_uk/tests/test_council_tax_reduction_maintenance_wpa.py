"""Statutory CTR income and disregards, independently calculated at 52 weeks.

England: SI 2012/2885 Sch 1 para 16, Sch 5 paras 7/20; default SI
2012/2886 Sch para 54, Sch 8 paras 21/49. Wales: WSI 2013/3029 Sch 1
para 10, Sch 6 para 17, Sch 4 paras 7/20, Sch 9 paras 21/49; default
WSI 2013/3035 Sch 5 paras 7/20, Sch 7 paras 21/49. Scotland: SSI
2021/249 reg 57(1)(b)(vi), (d), (4), (6); SSI 2012/319 reg 27(1)(j),
(o), Sch 3 paras 6/19. Wales's family premium applies to a family with
a child or young person (3029 Sch 1 para 1(1)(c) and Sch 2 para 3; at
working age, Sch 6 para 1(1)(c) and Sch 7 para 4).

Scottish and Welsh working-age awards select
council_tax_reduction_working_age_applicable_income (WSI 2013/3029 Sch 9
paras 21/49, Sch 6 para 1(1)(c); SSI 2021/249 reg 57(4), (6)). Within that
calculation, Welsh Universal Credit claims select the Universal Credit
income figure, so the working-age tests below pin the route without
Universal Credit. The different £15 disregard methods matter when WPA is
below £15 a week and Scotland counts other unearned income; Welsh claims
without Universal Credit also deduct tax on the allowance.
"""

import pytest

from policyengine_uk import Simulation

YEAR = 2026
AREAS = {
    "ENGLAND": ("LONDON", "WESTMINSTER"),
    "WALES": ("WALES", "CARDIFF"),
    "SCOTLAND": ("SCOTLAND", "GLASGOW_CITY"),
}
pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def family(
    country,
    *,
    age=40,
    recipient="claimant",
    maintenance=0,
    wpa=0,
    child=False,
    child_maintenance=0,
    route="general",
    head_applies_alone=False,
):
    people = {
        "claimant": {
            "age": age,
            "is_claimant_or_partner": True,
            "is_household_head": True,
            "state_pension": 0,
        },
        "partner": {
            "age": age,
            "is_claimant_or_partner": True,
            "is_household_head": False,
            "state_pension": 0,
        },
        "other": {
            "age": 22,
            "is_claimant_or_partner": False,
            "is_household_head": False,
        },
    }
    if child:
        people["child"] = {
            "age": 5,
            "is_claimant_or_partner": False,
            "is_household_head": False,
        }
    people[recipient].update(
        spousal_maintenance_income=maintenance,
        widowed_parents_allowance_reported=wpa,
        maintenance_income=child_maintenance,
    )
    region, authority = AREAS[country]
    # Pin the route and other awards to isolate the statutory income list.
    # Reported WPA is deliberate even at pension age: its statutory income
    # treatment also applies to an under-pension-age partner's payment.
    benunit = {
        "members": list(people),
        "council_tax_reduction_pensioner": age >= 67,
        "council_tax_reduction_head_applies_alone": head_applies_alone,
        "child_benefit": 0,
        "tax_credits": 0,
        "universal_credit": 0,
        "income_support": 0,
        "in_receipt_of_guarantee_credit": route == "guarantee",
        "in_receipt_of_savings_credit_only": route == "savings",
        "pension_credit_income": 13_000 if route == "savings" else 0,
        "pension_credit": 200 if route == "savings" else 0,
        "pension_credit_war_pension_income": 0,
    }
    return Simulation(
        situation={
            "people": {
                name: {key: {YEAR: value} for key, value in inputs.items()}
                for name, inputs in people.items()
            },
            "benunits": {
                "family": {
                    key: value if key == "members" else {YEAR: value}
                    for key, value in benunit.items()
                }
            },
            "households": {
                "home": {
                    "members": list(people),
                    "region": region,
                    "local_authority": authority,
                }
            },
        }
    )


def income(sim):
    return float(sim.calculate("council_tax_reduction_applicable_income", YEAR)[0])


@pytest.mark.parametrize("country", AREAS)
@pytest.mark.parametrize("age", [40, 80])
@pytest.mark.parametrize("recipient", ["claimant", "partner"])
def test_general_rules_count_wpa_after_fifteen_pounds_weekly(country, age, recipient):
    # £156.65 * 52 = £8,145.80; less £15 * 52 = £780 gives £7,365.80.
    sim = family(country, age=age, recipient=recipient, wpa=8_145.80)
    assert income(sim) == pytest.approx(7_365.80, abs=0.01)


@pytest.mark.parametrize("country", AREAS)
@pytest.mark.parametrize("age", [40, 80])
@pytest.mark.parametrize("child, expected", [(False, 5_200), (True, 4_420)])
def test_maintenance_disregard_depends_on_the_family(country, age, child, expected):
    # £100/week counts in full without a child; (£100 - £15)*52 otherwise.
    sim = family(country, age=age, maintenance=5_200, child=child)
    assert income(sim) == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("country", AREAS)
def test_maintenance_payments_share_one_family_disregard(country):
    sim = family(country, maintenance=2_600, child=True)
    sim.set_input("spousal_maintenance_income", YEAR, [2_600, 2_600, 0, 0])
    assert income(sim) == pytest.approx(4_420, abs=0.01)


@pytest.mark.parametrize("country", AREAS)
def test_small_payments_are_not_over_disregarded(country):
    assert income(family(country, maintenance=500, wpa=500, child=True)) == 0


@pytest.mark.parametrize("country", AREAS)
def test_only_applicant_partner_income_counts_and_child_maintenance_is_excluded(
    country,
):
    assert (
        income(family(country, recipient="other", maintenance=5_200, wpa=8_145.80)) == 0
    )
    assert income(family(country, child_maintenance=5_200, child=True)) == 0
    assert (
        income(
            family(
                country, recipient="child", child=True, maintenance=5_200, wpa=8_145.80
            )
        )
        == 0
    )


@pytest.mark.parametrize("country", AREAS)
def test_head_applying_alone_has_no_partner_or_child_disregard(country):
    assert (
        income(
            family(
                country, recipient="partner", maintenance=5_200, head_applies_alone=True
            )
        )
        == 0
    )
    assert income(
        family(country, maintenance=5_200, child=True, head_applies_alone=True)
    ) == pytest.approx(5_200)


@pytest.mark.parametrize("country", AREAS)
def test_guarantee_credit_still_passports_the_whole_income(country):
    sim = family(country, age=80, maintenance=5_200, wpa=8_145.80, route="guarantee")
    assert income(sim) == 0


@pytest.mark.parametrize("country", AREAS)
@pytest.mark.parametrize("child, expected", [(False, 13_200), (True, 12_420)])
def test_savings_credit_uses_assessed_income_without_adding_maintenance_again(
    country, child, expected
):
    # The Secretary of State's £13,000 already contains £5,200 maintenance.
    # Add £200 savings credit and subtract only CTR's child-family disregard.
    sim = family(country, age=80, maintenance=5_200, child=child, route="savings")
    assert income(sim) == pytest.approx(expected, abs=0.01)


DEVOLVED = ["WALES", "SCOTLAND"]


def working_age_family(country, **inputs):
    """A family on the devolved route without Universal Credit, which the
    model would otherwise award where the family has little other income."""
    sim = family(country, **inputs)
    sim.set_input(
        "council_tax_reduction_working_age_has_universal_credit", YEAR, [False]
    )
    return sim


def working_age_income(sim):
    return float(
        sim.calculate("council_tax_reduction_working_age_applicable_income", YEAR)[0]
    )


def working_age_rise(country, **inputs):
    """Rise in working-age income over the same family without the
    maintenance, WPA and child maintenance in the inputs."""
    without = {
        key: value
        for key, value in inputs.items()
        if key not in ("maintenance", "wpa", "child_maintenance")
    }
    return working_age_income(
        working_age_family(country, **inputs)
    ) - working_age_income(working_age_family(country, **without))


@pytest.mark.parametrize("country", DEVOLVED)
@pytest.mark.parametrize("recipient", ["claimant", "partner"])
@pytest.mark.parametrize("child, maintenance_counted", [(False, 5_200), (True, 4_420)])
def test_working_age_route_counts_maintenance_and_wpa(
    country, recipient, child, maintenance_counted
):
    # Without Universal Credit. £100/week maintenance counts in full without a
    # child, (£100 - £15) * 52 with one; WPA £8,145.80 - £780 = £7,365.80.
    rise = working_age_rise(
        country, recipient=recipient, maintenance=5_200, wpa=8_145.80, child=child
    )
    assert rise == pytest.approx(maintenance_counted + 7_365.80, abs=0.01)


@pytest.mark.parametrize("country", DEVOLVED)
def test_working_age_route_shares_one_maintenance_disregard(country):
    sim = working_age_family(country, child=True)
    base = working_age_income(sim)
    sim = working_age_family(country, child=True)
    sim.set_input("spousal_maintenance_income", YEAR, [2_600, 2_600, 0, 0])
    assert working_age_income(sim) - base == pytest.approx(4_420, abs=0.01)


@pytest.mark.parametrize("country", DEVOLVED)
def test_working_age_route_does_not_over_disregard_small_payments(country):
    assert working_age_rise(country, maintenance=500, wpa=500, child=True) == 0


@pytest.mark.parametrize("country, expected", [("WALES", 14_820), ("SCOTLAND", 14_560)])
def test_working_age_small_wpa_disregard_reaches_other_income_only_in_scotland(
    country, expected
):
    # Maintenance £300/week less £15 = £14,820; WPA £10/week. Wales disregards
    # the whole allowance and stops; Scotland counts it, 14,820 + 520, and
    # takes £780 from the total (SSI 2021/249 reg 57(4)).
    rise = working_age_rise(country, maintenance=15_600, wpa=520, child=True)
    assert rise == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("country", DEVOLVED)
def test_working_age_small_wpa_disregard_does_not_reach_earnings(country):
    # Reg 57(4) takes £15 a week from unearned income only, and Wales from the
    # allowance itself, so a £10/week allowance leaves earnings untouched.
    def with_earnings(**inputs):
        sim = working_age_family(country, **inputs)
        sim.set_input("employment_income", YEAR, [10_000, 0, 0])
        return working_age_income(sim)

    assert with_earnings() > 0
    assert with_earnings(wpa=520) == pytest.approx(with_earnings(), abs=0.01)


@pytest.mark.parametrize("country", DEVOLVED)
def test_working_age_wpa_disregard_needs_an_applicant_or_partner_recipient(country):
    # A non-dependant's allowance does not count and brings no disregard for
    # the claimant's maintenance (no child, so all £5,200 counts).
    sim = working_age_family(country, maintenance=5_200)
    sim.set_input("widowed_parents_allowance_reported", YEAR, [0, 0, 8_145.80])
    assert working_age_income(sim) == pytest.approx(5_200, abs=0.01)


@pytest.mark.parametrize("country", DEVOLVED)
def test_working_age_route_counts_only_applicant_and_partner_and_no_child_maintenance(
    country,
):
    assert working_age_rise(country, recipient="other", maintenance=5_200) == 0
    assert working_age_rise(country, recipient="other", wpa=8_145.80) == 0
    assert working_age_rise(country, child_maintenance=5_200, child=True) == 0
    assert (
        working_age_rise(
            country, recipient="child", child=True, maintenance=5_200, wpa=8_145.80
        )
        == 0
    )


@pytest.mark.parametrize("country", DEVOLVED)
def test_working_age_head_applying_alone_has_no_partner_or_child_disregard(country):
    assert (
        working_age_rise(
            country, recipient="partner", maintenance=5_200, head_applies_alone=True
        )
        == 0
    )
    assert (
        working_age_rise(
            country, recipient="partner", wpa=8_145.80, head_applies_alone=True
        )
        == 0
    )
    assert working_age_rise(
        country, maintenance=5_200, child=True, head_applies_alone=True
    ) == pytest.approx(5_200, abs=0.01)
    # The excluded partner's allowance brings no disregard against the head's
    # maintenance, which counts in full without a child in the assessment.
    sim = working_age_family(country, maintenance=5_200, head_applies_alone=True)
    sim.set_input("widowed_parents_allowance_reported", YEAR, [0, 8_145.80, 0])
    assert working_age_income(sim) == pytest.approx(5_200, abs=0.01)
