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


@pytest.mark.parametrize("year", [2026, 2027, 2028, 2029, 2030])
def test_scottish_announced_threshold_freeze_then_cpi_projection(year):
    # Scottish Budget 2026-27, Income Tax Policy: the higher, advanced and
    # top cash thresholds stay fixed through 2028-29. Future CPI uprating
    # is the model's existing projection, not a Budget commitment.
    # https://www.gov.scot/publications/scottish-budget-2026-2027/pages/4/
    rates = system.parameters.gov.hmrc.income_tax.rates.scotland.rates(year)
    cpi = system.parameters.gov.economic_assumptions.indices.obr.consumer_price_index
    after_freeze = 1 if year <= 2028 else cpi(year) / cpi(2028)

    assert rates.thresholds[3:] == pytest.approx(
        [amount * after_freeze for amount in (31_092, 62_430, 125_140)], abs=1e-6
    )
    # Lower bands retain their pre-existing projection from the 2026 values.
    assert rates.thresholds[:3] == pytest.approx(
        [0, 3_967 * cpi(year) / cpi(2026), 16_956 * cpi(year) / cpi(2026)],
        abs=1e-6,
    )
    assert rates.rates == [0.19, 0.20, 0.21, 0.42, 0.45, 0.48]
