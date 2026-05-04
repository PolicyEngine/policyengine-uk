from policyengine_uk.model_api import *
import numpy as np


class cheshire_west_and_chester_council_tax_reduction_war_pensioner_tariff_income(
    Variable
):
    value_type = float
    entity = BenUnit
    label = "Cheshire West and Chester Council Tax Reduction war pensioner tariff income from capital"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.cheshire_west_and_chester.council_tax_reduction
        war_pensioner = benunit(
            "cheshire_west_and_chester_council_tax_reduction_war_pensioner", period
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        tariff = ctr.means_test.tariff_income
        excess_capital = max_(0, capital - tariff.threshold)
        tariff_units = np.ceil(excess_capital / tariff.step)
        return war_pensioner * tariff_units * tariff.amount * WEEKS_IN_YEAR
