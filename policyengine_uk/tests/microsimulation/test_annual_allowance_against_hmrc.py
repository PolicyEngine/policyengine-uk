"""The 2024-25 annual allowance charge on the certified dataset against HMRC.

HMRC, Private pension statistics (July 2026), 2024-25 provisional:
- Table 7: 30,440 individuals reported pension contributions exceeding their
  annual allowance through Self Assessment. Self Assessment reports only the
  excess over the allowance after unused allowance is carried forward (HMRC,
  HS345 Pension savings tax charges, 2025).
- Table 6: annual allowance charges of £0.3bn, rounded to the nearest £0.1bn.

The model's count of payers and its charge in 2024 must each lie within half
to one and a half times these. The certified Enhanced FRS imputes employer
pension contributions as three times employee contributions
(PolicyEngine/policyengine-uk-data#606), which puts both several times above
HMRC's, so this is a strict expected failure until the dataset fixes that. The
test reports no model value: the counts rest on survey records.
"""

import pytest

from policyengine_uk import Microsimulation

YEAR = 2024
HMRC_PAYERS = 30_440
HMRC_CHARGE = 0.3e9
TOLERANCE = 0.5


def _within(value, target):
    return (1 - TOLERANCE) * target <= value <= (1 + TOLERANCE) * target


@pytest.mark.microsimulation
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="PolicyEngine/policyengine-uk-data#606: employer pension "
    "contributions imputed as three times employee contributions",
)
def test_2024_annual_allowance_charge_and_payers_are_near_hmrc():
    charge = Microsimulation().calculate("personal_pension_contributions_tax", YEAR)
    near_hmrc = bool(
        _within((charge > 0).sum(), HMRC_PAYERS) and _within(charge.sum(), HMRC_CHARGE)
    )
    assert near_hmrc, "The 2024 annual allowance charge is outside HMRC's band."
