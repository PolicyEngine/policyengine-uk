"""The High Value Council Tax Surcharge falls on owners, not occupiers (#2141).

Budget 2025's policy paper and the May 2026 MHCLG consultation both say
"owners, rather than occupiers" are liable. The model charges a household only
on the main residence it owns, so an otherwise identical household that rents
the same home owes nothing.
"""

import pytest

from policyengine_uk import Simulation

OWNER_TENURES = ["OWNED_OUTRIGHT", "OWNED_WITH_MORTGAGE"]
RENTER_TENURES = ["RENT_PRIVATELY", "RENT_FROM_COUNCIL", "RENT_FROM_HA"]


def surcharge(tenure, value, region="LONDON", year=2028):
    household = {
        "members": ["adult"],
        "region": {year: region},
        "main_residence_value": {year: value},
    }
    if tenure is not None:
        household["tenure_type"] = {year: tenure}
    sim = Simulation(
        situation={
            "people": {"adult": {"age": {year: 50}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {"household": household},
        }
    )
    return float(sim.calculate("high_value_council_tax_surcharge", year)[0])


@pytest.mark.parametrize("value", [3_000_000, 4_000_000, 8_000_000])
def test_only_owners_are_charged_for_the_same_home(value):
    owner_charges = {surcharge(tenure, value) for tenure in OWNER_TENURES}
    assert len(owner_charges) == 1
    assert owner_charges.pop() > 0
    for tenure in RENTER_TENURES:
        assert surcharge(tenure, value) == 0, tenure


def test_unspecified_tenure_takes_the_renting_default():
    assert surcharge(None, 8_000_000) == 0


def test_owners_outside_england_are_not_charged():
    for region in ["SCOTLAND", "WALES", "NORTHERN_IRELAND"]:
        assert surcharge("OWNED_OUTRIGHT", 8_000_000, region=region) == 0
