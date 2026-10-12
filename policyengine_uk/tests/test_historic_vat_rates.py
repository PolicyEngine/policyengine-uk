import pytest

from policyengine_uk import CountryTaxBenefitSystem


def test_reduced_vat_rate_history():
    reduced_rate = CountryTaxBenefitSystem().parameters.gov.hmrc.vat.reduced_rate

    assert reduced_rate("1994-04-01") == pytest.approx(0.08)
    assert reduced_rate("1997-08-31") == pytest.approx(0.08)
    assert reduced_rate("1997-09-01") == pytest.approx(0.05)
