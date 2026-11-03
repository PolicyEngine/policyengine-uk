import pytest

from policyengine_uk import CountryTaxBenefitSystem


def test_tax_credits_withdrawal_rate_changed_in_2011():
    rate = CountryTaxBenefitSystem().parameters.gov.dwp.tax_credits.means_test.income_reduction_rate

    assert rate("2011-04-05") == pytest.approx(0.39)
    assert rate("2011-04-06") == pytest.approx(0.41)
