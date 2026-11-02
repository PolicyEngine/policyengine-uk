from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.model_api import GBP


def test_free_tv_licence_value_uses_currency_units():
    system = CountryTaxBenefitSystem()

    assert system.variables["free_tv_licence_value"].unit == GBP
