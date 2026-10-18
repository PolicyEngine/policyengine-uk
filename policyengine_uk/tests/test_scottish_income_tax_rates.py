import pytest

from policyengine_uk.system import system


@pytest.mark.parametrize(
    "year, thresholds",
    [
        # Scottish Rate Resolutions S6M-12252, S6M-16531 and S6M-20844.
        (2024, [0, 2306, 13991, 31092, 62430, 125140]),
        (2025, [0, 2827, 14921, 31092, 62430, 125140]),
        (2026, [0, 3967, 16956, 31092, 62430, 125140]),
    ],
)
def test_scottish_income_tax_thresholds_match_the_resolution(year, thresholds):
    rates = system.parameters.gov.hmrc.income_tax.rates.scotland.rates(f"{year}-04-06")

    assert rates.thresholds == thresholds
