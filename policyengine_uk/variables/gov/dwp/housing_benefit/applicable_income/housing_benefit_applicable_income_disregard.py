from policyengine_uk.model_api import *


class housing_benefit_applicable_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit earnings disregards"
    documentation = "Ordinary, special, permitted-work and accommodation earnings disregards, plus the additional earnings amount when its work and coverage conditions hold. The coverage comparison includes earnings-limited childcare. Savings-credit-only cases retain Pension Credit grounds. Passported earnings are disregarded in full."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/157/regulation/2",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        earnings = benunit("housing_benefit_net_earnings", period)
        base = benunit("housing_benefit_pre_additional_earnings_disregard", period)
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
        amount = p.worker * WEEKS_IN_YEAR
        # Compare in pence: exact equality can otherwise fail in float32.
        covers = np.round(earnings.astype(float), 2) >= np.round(
            (base + childcare + amount).astype(float), 2
        )
        additional = where(
            benunit(
                "meets_housing_benefit_additional_earnings_disregard_conditions", period
            )
            & covers,
            amount,
            0,
        )
        return where(
            benunit("housing_benefit_on_passporting_benefit", period),
            earnings,
            base + additional,
        )
