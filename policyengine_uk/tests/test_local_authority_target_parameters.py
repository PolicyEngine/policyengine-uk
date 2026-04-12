from policyengine_uk.system import system


def test_local_authority_target_uprating_parameters():
    params = system.parameters.gov.economic_assumptions.local_authority_targets
    ons_income = params.ons_income

    assert ons_income.net_income_bhc_uprating_factor("2025-01-01") == (1985.1 / 1467.6)
    assert ons_income.housing_costs_uprating_factor("2025-01-01") == (103.5 / 84.9)

    bhc_reference = ons_income.net_income_bhc_uprating_factor.metadata["reference"][0]
    housing_reference = ons_income.housing_costs_uprating_factor.metadata["reference"][
        0
    ]

    assert "November 2025" in bhc_reference["title"]
    assert "November 2025" in housing_reference["title"]
