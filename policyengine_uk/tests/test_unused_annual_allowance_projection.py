"""A stored unused annual allowance is for its own year only (#2523).

Unused allowance carried forward (Finance Act 2004 s. 228A) comes from the
three tax years before the one it is for, a window that moves each year. So a
dataset's stored value stays in its own year, and each projected year uses the
variable's estimate instead of a copy.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset

STORED = 50_000.0


def _dataset(stored=None):
    ids = np.arange(1, 2)
    person = {
        "person_id": ids,
        "person_benunit_id": ids,
        "person_household_id": ids,
        "age": 45,
        "employment_income": 100_000.0,
        "employer_pension_contributions": 70_000.0,
    }
    if stored is not None:
        person["unused_pension_annual_allowance"] = stored
    return UKSingleYearDataset(
        person=pd.DataFrame(person),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": 1.0,
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
            }
        ),
        fiscal_year=2024,
    )


def test_projected_years_do_not_copy_a_stored_unused_allowance():
    extended = extend_single_year_dataset(_dataset(STORED), parameters, end_year=2027)

    assert extended[2024].person["unused_pension_annual_allowance"].tolist() == [STORED]
    for year in (2025, 2026, 2027):
        assert "unused_pension_annual_allowance" not in extended[year].person.columns


def test_a_projected_year_uses_the_estimate_not_the_stored_value():
    stored = Microsimulation(dataset=_dataset(STORED))
    estimated = Microsimulation(dataset=_dataset())

    assert stored.calculate("unused_pension_annual_allowance", 2024).values == (
        pytest.approx([STORED])
    )
    # Saving 70,000 a year, grown with pay, exceeds each earlier allowance, so
    # the estimate for 2026 carries nothing forward; a copy would give 50,000.
    assert stored.calculate(
        "unused_pension_annual_allowance", 2026
    ).values == pytest.approx(
        estimated.calculate("unused_pension_annual_allowance", 2026).values
    )
    assert stored.calculate("unused_pension_annual_allowance", 2026).values[0] == 0
