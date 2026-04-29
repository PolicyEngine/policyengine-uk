from policyengine_uk import CountryTaxBenefitSystem


def test_legacy_benefit_age_threshold_parameters():
    params = CountryTaxBenefitSystem().parameters

    assert params.gov.dwp.JSA.eligibility.min_age("2025") == 18
    assert params.gov.dwp.ESA.eligibility.min_age("2025") == 16


def test_jsa_hours_parameter_still_exposed():
    params = CountryTaxBenefitSystem().parameters

    assert params.gov.dwp.JSA.hours.single("2025") == 16
