from policyengine_uk.system import system


def test_scottish_income_tax_thresholds_updated_for_2026():
    rates = system.parameters.gov.hmrc.income_tax.rates.scotland.rates("2026-04-06")

    assert rates.thresholds == [0.0, 3967, 16956, 31092, 62430, 112570]
