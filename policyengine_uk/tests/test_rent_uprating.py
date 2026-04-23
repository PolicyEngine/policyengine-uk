from types import SimpleNamespace

import pandas as pd
import pytest

from policyengine_uk import parameters
from policyengine_uk.data.economic_assumptions import uprate_rent


def test_uprate_rent_uses_tenure_specific_growth():
    previous_year = SimpleNamespace(
        household=pd.DataFrame({"rent": [1_000.0, 1_000.0]})
    )
    current_year = SimpleNamespace(
        time_period="2025",
        household=pd.DataFrame(
            {
                "tenure_type": ["RENT_PRIVATELY", "RENT_FROM_COUNCIL"],
                "region": ["LONDON", "LONDON"],
                "rent": [0.0, 0.0],
            }
        ),
    )

    uprate_rent(current_year, previous_year, parameters)

    assert current_year.household["rent"][0] == pytest.approx(1_066.484)
    assert current_year.household["rent"][1] == pytest.approx(1_080.0)
