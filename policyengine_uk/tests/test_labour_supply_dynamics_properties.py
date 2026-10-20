"""Property-based tests for Simulation.apply_dynamics (progression responses).

For any households and any change to the basic rate of income tax, with the
OBR labour supply assumptions on:

1. People excluded from responses keep their employment income. They are
   people under 18, aged 60 or over, self-employed, students, and adults
   beyond the two oldest in their household. The oracle below computes this
   independently of the model.
2. The report has one row per included person and no NaN.
3. Each included person's employment income moves by exactly the total
   response the report gives them, and the total response is the sum of the
   substitution and income responses.
4. With no policy change every response is zero.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario

YEAR = 2025
BASELINE_BASIC_RATE = 0.20
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
STATUSES = ["FT_EMPLOYED", "FT_SELF_EMPLOYED", "STUDENT"]
EXCLUDED_STATUSES = {"FT_SELF_EMPLOYED", "STUDENT"}


@st.composite
def households(draw):
    # Distinct ages, so the ranking of adults by age is unambiguous.
    ages = draw(st.lists(st.integers(18, 75), min_size=1, max_size=3, unique=True))
    adults = [
        dict(
            age=age,
            employment_income=draw(st.sampled_from([0, 8_000, 25_000, 60_000])),
            gender=draw(st.sampled_from(["MALE", "FEMALE"])),
            employment_status=draw(st.sampled_from(STATUSES)),
        )
        for age in ages
    ]
    children = draw(st.lists(st.integers(0, 17), max_size=2))
    return dict(adults=adults, children=children, married=draw(st.booleans()))


@st.composite
def scenarios(draw):
    return dict(
        basic_rate=draw(st.sampled_from([BASELINE_BASIC_RATE, 0.15, 0.25, 0.30])),
        households=draw(st.lists(households(), min_size=1, max_size=3)),
    )


def build(scenario):
    """The situation, each person's employment income, and the oracle."""
    people, benunits, households_ = {}, {}, {}
    income, excluded = [], []
    for h, household in enumerate(scenario["households"]):
        adult_names, child_names = [], []
        oldest_two = sorted(a["age"] for a in household["adults"])[-2:]
        for a, adult in enumerate(household["adults"]):
            name = f"h{h}_adult_{a}"
            people[name] = dict(
                adult,
                hours_worked=1_800 if adult["employment_income"] > 0 else 0,
            )
            adult_names.append(name)
            income.append(adult["employment_income"])
            excluded.append(
                adult["age"] >= 60
                or adult["employment_status"] in EXCLUDED_STATUSES
                or adult["age"] not in oldest_two
            )
        for c, age in enumerate(household["children"]):
            name = f"h{h}_child_{c}"
            people[name] = {"age": age}
            child_names.append(name)
            income.append(0)
            excluded.append(True)
        # The first two adults and the children form one benefit unit; a
        # third adult has their own.
        benunits[f"h{h}_family"] = {
            "members": adult_names[:2] + child_names,
            "is_married": household["married"] and len(adult_names) > 1,
        }
        if len(adult_names) == 3:
            benunits[f"h{h}_other"] = {"members": [adult_names[2]]}
        households_[f"h{h}"] = {"members": adult_names + child_names}
    situation = {"people": people, "benunits": benunits, "households": households_}
    return situation, np.array(income, dtype=float), np.array(excluded)


@PROPERTY_SETTINGS
@given(scenarios())
def test_dynamics_respond_only_for_included_people(scenario):
    situation, income, excluded = build(scenario)
    reformed = Microsimulation(
        situation=situation,
        scenario=Scenario(
            parameter_changes={
                "gov.hmrc.income_tax.rates.uk[0].rate": {
                    str(YEAR): scenario["basic_rate"]
                },
                "gov.dynamic.obr_labour_supply_assumptions": {str(YEAR): True},
            }
        ),
    )
    dynamics = reformed.apply_dynamics(YEAR)
    after = np.asarray(reformed.calculate("employment_income", YEAR), dtype=float)
    progression = dynamics.progression

    # 1. Excluded people keep their employment income.
    np.testing.assert_allclose(after[excluded], income[excluded], atol=0.01)

    # 2. One row per included person, and no NaN.
    assert len(progression) == (~excluded).sum()
    report = np.asarray(progression, dtype=float)
    assert not np.isnan(report).any()

    # 3. Included people move by exactly their reported total response.
    total = np.asarray(progression["total_response"], dtype=float)
    np.testing.assert_allclose(
        total,
        np.asarray(progression["substitution_response"], dtype=float)
        + np.asarray(progression["income_response"], dtype=float),
        atol=1e-6,
    )
    # Employment income is stored as float32.
    np.testing.assert_allclose(
        after[~excluded], income[~excluded] + total, atol=0.01, rtol=1e-6
    )

    # 4. No policy change, no response.
    if scenario["basic_rate"] == BASELINE_BASIC_RATE:
        assert (total == 0).all()
