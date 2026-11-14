import pytest

from policyengine_uk import CountryTaxBenefitSystem


@pytest.mark.parametrize(
    ("date", "expected"),
    [
        ("2019-01-01", 1_104),
        ("2022-10-01", 3_549),
        ("2023-07-01", 2_074),
        ("2023-10-01", 1_834),
        ("2024-01-01", 1_928),
        ("2025-10-01", 1_755),
        ("2026-07-01", 1_663),
        ("2026-10-01", 1_723),
    ],
)
def test_energy_price_cap_uses_final_direct_debit_values(date, expected):
    parameters = CountryTaxBenefitSystem().parameters

    assert parameters.gov.ofgem.energy_price_cap(date) == expected
