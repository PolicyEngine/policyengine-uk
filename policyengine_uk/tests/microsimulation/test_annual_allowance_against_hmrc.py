"""The 2024-25 annual allowance charge on the certified dataset against HMRC.

HMRC, Private pension statistics (July 2026), 2024-25 provisional:
- Table 7: 30,440 individuals reported pension contributions exceeding their
  annual allowance through Self Assessment, with £672m of contributions above
  it. Self Assessment reports only the excess over the allowance after unused
  allowance is carried forward (HMRC, HS345 Pension savings tax charges, 2025).
- Table 6: annual allowance charges of £0.3bn, rounded to the nearest £0.1bn.

The model's count of payers, its charge and its chargeable amount in 2024 must
each lie within half to one and a half times these. The excess does not depend
on marginal rates, so it is the cleaner of the two amounts.

On the certified Enhanced FRS all three are several times HMRC's. The known
data gaps behind that are chiefly policyengine-uk-data#606: the dataset
imputes employer pension contributions as three times employee contributions.
With employer contributions at a third of their stored values all three fall
within the band, so this is a strict expected failure until the data is
fixed. The test reports no model value: the counts rest on survey records.
"""

import pytest

from policyengine_uk import Microsimulation

YEAR = 2024
HMRC_PAYERS = 30_440
HMRC_EXCESS = 672e6
HMRC_CHARGE = 0.3e9
TOLERANCE = 0.5


def _within(value, target):
    return (1 - TOLERANCE) * target <= value <= (1 + TOLERANCE) * target


@pytest.mark.microsimulation
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Known data gaps, chiefly PolicyEngine/policyengine-uk-data#606: "
    "employer pension contributions imputed as three times employee "
    "contributions",
)
def test_2024_annual_allowance_charge_and_payers_are_near_hmrc():
    sim = Microsimulation()
    charge = sim.calculate("personal_pension_contributions_tax", YEAR)
    excess = sim.calculate("pension_annual_allowance_chargeable_amount", YEAR)
    near_hmrc = bool(
        _within((charge > 0).sum(), HMRC_PAYERS)
        and _within(charge.sum(), HMRC_CHARGE)
        and _within(excess.sum(), HMRC_EXCESS)
    )
    assert near_hmrc, "The 2024 annual allowance charge is outside HMRC's band."
