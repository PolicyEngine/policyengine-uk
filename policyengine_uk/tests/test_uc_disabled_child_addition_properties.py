"""UC reg 24(2): one disabled-child tier, with an independent blind limb.

The exact award categories provide the entitlement classification oracle.
The amount-only checks separately preserve the existing, nonstatutory paid-
amount proxy; they do not establish entitlement from part-year payments.
Generated reported categories test the conditional input contract, not the
underlying age or overlapping-award eligibility of each generated combination.
2026 cash anchors are the unchanged monthly amounts 164.79 and 514.71.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import WEEKS_IN_YEAR

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2026
LOWER = 1_977.48
HIGHER = 6_176.52


def family(child, reverse=False):
    people = {
        "parent": {
            "age": {YEAR: 35},
            "is_parent": {YEAR: True},
            "is_benunit_head": {YEAR: True},
        },
        "child": {
            "age": {YEAR: 8},
            "is_benunit_head": {YEAR: False},
            **{name: {YEAR: value} for name, value in child.items()},
        },
    }
    names = list(people)
    if reverse:
        people = dict(reversed(list(people.items())))
        names.reverse()
    return {
        "people": people,
        "benunits": {"family": {"members": names}},
        "households": {"home": {"members": names}},
    }


def child_additions(sim):
    ids = list(sim.populations["person"].ids)
    child = ids.index("child")
    return (
        sim.calculate("uc_individual_disabled_child_element", YEAR)[child],
        sim.calculate("uc_individual_severely_disabled_child_element", YEAR)[child],
    )


@settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    age=st.integers(0, 15),
    dla=st.sampled_from(["NONE", "LOWER", "MIDDLE", "HIGHER"]),
    pip=st.sampled_from(["NONE", "STANDARD", "ENHANCED"]),
    blind=st.booleans(),
    lower_flag=st.booleans(),
    reverse=st.booleans(),
)
def test_exact_award_categories_and_blindness_select_one_tier(
    age, dla, pip, blind, lower_flag, reverse
):
    sim = Simulation(
        situation=family(
            {
                "age": age,
                "dla_sc_category": dla,
                "pip_dl_category": pip,
                "is_blind": blind,
                "is_disabled_for_benefits": lower_flag,
            },
            reverse=reverse,
        )
    )
    higher = blind or dla == "HIGHER" or pip == "ENHANCED"
    expected = (LOWER if lower_flag and not higher else 0, HIGHER if higher else 0)
    actual = child_additions(sim)
    np.testing.assert_allclose(actual, expected, atol=0.01, rtol=0)
    assert not (actual[0] > 0 and actual[1] > 0)
    # Claimant roles remain excluded, even when entity/member order changes.
    parent = list(sim.populations["person"].ids).index("parent")
    for variable in (
        "uc_individual_disabled_child_element",
        "uc_individual_severely_disabled_child_element",
    ):
        assert sim.calculate(variable, YEAR)[parent] == 0


@pytest.mark.parametrize(
    "awards, higher",
    [
        ({"dla_sc": (114.6 - 10) * WEEKS_IN_YEAR - 1}, False),
        ({"dla_sc": (114.6 - 10) * WEEKS_IN_YEAR}, True),
        ({"pip_dl": (114.6 - 10) * WEEKS_IN_YEAR + 1}, True),
        ({"dla_sc_category": "HIGHER", "dla_sc": 0}, False),
        ({"pip_dl_category": "ENHANCED", "pip_dl": 0}, False),
    ],
    ids=[
        "DLA-below-proxy",
        "DLA-at-proxy",
        "PIP-above-proxy",
        "DLA-direct-zero",
        "PIP-direct-zero",
    ],
)
def test_existing_direct_amount_proxy_and_override_precedence(awards, higher):
    # Weekly 114.60 is the existing 2026 high/enhanced rate; 10 is the
    # retained modeling tolerance, not a statutory entitlement threshold.
    sim = Simulation(situation=family({**awards, "is_disabled_for_benefits": True}))
    np.testing.assert_allclose(
        child_additions(sim),
        (0, HIGHER) if higher else (LOWER, 0),
        atol=0.01,
        rtol=0,
    )


def test_zero_higher_rate_reform_does_not_pay_the_lower_tier_instead():
    reform = Reform.from_dict(
        {
            "gov.dwp.universal_credit.elements.child.severely_disabled.amount": {
                "2026-01-01.2026-12-31": 0
            }
        },
        country_id="uk",
    )
    sim = Simulation(
        situation=family(
            {"dla_sc_category": "HIGHER", "is_disabled_for_benefits": True}
        ),
        reform=reform,
    )
    np.testing.assert_array_equal(child_additions(sim), [0, 0])


def test_amount_proxy_tolerance_is_configurable_without_changing_award_rates():
    reform = Reform.from_dict(
        {
            "gov.dwp.universal_credit.elements.child.severely_disabled.benefit_amount_tolerance": {
                "2026-01-01.2026-12-31": 0
            }
        },
        country_id="uk",
    )
    sim = Simulation(
        situation=family(
            {"dla_sc": (114.6 - 10) * WEEKS_IN_YEAR, "is_disabled_for_benefits": True}
        ),
        reform=reform,
    )
    np.testing.assert_allclose(child_additions(sim), [LOWER, 0], atol=0.01, rtol=0)
