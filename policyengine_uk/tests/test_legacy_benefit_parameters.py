from policyengine_uk import CountryTaxBenefitSystem


def test_legacy_benefit_age_threshold_parameters():
    params = CountryTaxBenefitSystem().parameters

    assert params.gov.dwp.JSA.eligibility.min_age("2025") == 18
    assert params.gov.dwp.ESA.eligibility.min_age("2025") == 16


def test_jsa_hours_parameter_still_exposed():
    params = CountryTaxBenefitSystem().parameters

    assert params.gov.dwp.JSA.hours.single("2025") == 16


def test_income_support_remunerative_work_hours_by_date():
    # IS Regs 1987 reg 5(1): 24 hours as made, 16 from 7 April 1992; reg 5(1A),
    # inserted from 7 October 1996, makes it 24 for the partner.
    work = CountryTaxBenefitSystem().parameters.gov.dwp.income_support.eligibility
    work = work.remunerative_work
    expected = {
        "1990-01-01": (24, 24),
        "1992-04-06": (24, 24),
        "1992-04-07": (16, 16),
        "1996-10-06": (16, 16),
        "1996-10-07": (16, 24),
        "2025-01-01": (16, 24),
    }
    for date, (claimant, partner) in expected.items():
        assert work.claimant_hours(date) == claimant, date
        assert work.partner_hours(date) == partner, date
