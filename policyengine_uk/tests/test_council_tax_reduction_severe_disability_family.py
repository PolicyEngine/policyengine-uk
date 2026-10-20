"""CTR family-mask input contracts, separate from derived eligibility tests.

SSI 2021/249 regs 6 and 8(2)(a), Sch 1 para 13 retain an applicant's
UC young person in their family. These finite grids deliberately supply the
two young-person statuses to exercise both directions independently of the
upstream eligibility rules. The policy YAML uses school/course inputs and
the annual terminal-date input, plus actual PIP, pension and council tax.

Looked-after and other-benefit-unit treatment remains the existing model
baseline, not a certification of reg 8(2)(b) and its paragraph (3) overrides.
"""

from itertools import product

import numpy as np
import pytest

from policyengine_uk import Simulation


def input_grid(rows, country="SCOTLAND", year=2026, applicant_age=45):
    people, benunits, households = {}, {}, {}
    for i, row in enumerate(rows):
        applicant, student = f"a{i}", f"s{i}"
        people[applicant] = {
            "age": applicant_age,
            "is_claimant_or_partner": True,
            "pip_dl_category": "ENHANCED",
        }
        people[student] = {
            "age": row.get("age", 19),
            "is_claimant_or_partner": False,
            "is_child_or_qualifying_young_person_for_child_benefit": row["cb"],
            "is_qualifying_young_person_for_universal_credit": row["uc"],
            "is_looked_after_by_local_authority": row.get("looked_after", False),
            "is_blind": row.get("blind", False),
            "pip_dl_category": "STANDARD" if row.get("benefit", False) else "NONE",
        }
        members = [applicant, student]
        benunits[f"b{i}"] = {
            "members": [applicant] if row.get("other_bu", False) else members,
            "would_claim_uc": False,
            "would_claim_IS": False,
            "would_claim_pc": False,
        }
        if row.get("other_bu", False):
            benunits[f"other{i}"] = {"members": [student]}
        households[f"h{i}"] = {"members": members, "country": country}
    situation = {"people": people, "benunits": benunits, "households": households}
    # A situation's default period is the model default, not necessarily year.
    for group in situation.values():
        for values in group.values():
            for name, value in list(values.items()):
                if name != "members":
                    values[name] = {year: value}
    return Simulation(situation=situation), [f"b{i}" for i in range(len(rows))]


def values(sim, variable, names, year=2026):
    result = sim.calculate(variable, year)
    ids = list(sim.populations["benunit"].ids)
    return np.array([result[ids.index(name)] for name in names])


@pytest.mark.parametrize(
    "country,year,applicant_age,scottish_working_age",
    [
        ("SCOTLAND", 2026, 45, True),
        ("SCOTLAND", 2021, 45, False),
        ("SCOTLAND", 2026, 70, False),
        ("ENGLAND", 2026, 45, False),
        ("WALES", 2026, 45, False),
        ("NORTHERN_IRELAND", 2026, 45, False),
    ],
)
def test_own_family_status_contract_by_applicant_scheme(
    country, year, applicant_age, scottish_working_age
):
    rows = [
        dict(cb=cb, uc=uc, looked_after=looked_after)
        for cb, uc, looked_after in product([False, True], repeat=3)
    ]
    sim, names = input_grid(rows, country, year, applicant_age)
    expected = [
        not (
            row["uc"] if scottish_working_age and not row["looked_after"] else row["cb"]
        )
        for row in rows
    ]
    assert (
        values(
            sim,
            "has_non_dependant_for_council_tax_reduction_severe_disability_premium",
            names,
            year,
        ).tolist()
        == expected
    )
    # HB and IS retain the original Child Benefit family classification.
    assert values(
        sim, "has_non_dependant_for_severe_disability_premium", names, year
    ).tolist() == [not row["cb"] for row in rows]


def test_age_boundary_and_blind_or_benefit_exceptions():
    rows = [
        dict(age=age, cb=True, uc=False, blind=blind, benefit=benefit)
        for age, blind, benefit in product(
            [17.999, 18, 19, 20], [False, True], [False, True]
        )
    ]
    sim, names = input_grid(rows)
    expected = [
        row["age"] >= 18 and not row["blind"] and not row["benefit"] for row in rows
    ]
    assert (
        values(
            sim,
            "has_non_dependant_for_council_tax_reduction_severe_disability_premium",
            names,
        ).tolist()
        == expected
    )
    # The shared gate still disregards these own-BU Child Benefit young people.
    assert not values(
        sim, "has_non_dependant_for_severe_disability_premium", names
    ).any()


def test_other_benefit_units_keep_existing_treatment():
    rows = [
        dict(cb=cb, uc=uc, looked_after=looked_after, other_bu=True)
        for cb, uc, looked_after in product([False, True], repeat=3)
    ]
    sim, names = input_grid(rows)
    assert values(sim, "has_non_dependant_for_severe_disability_premium", names).all()
    assert values(
        sim,
        "has_non_dependant_for_council_tax_reduction_severe_disability_premium",
        names,
    ).all()
