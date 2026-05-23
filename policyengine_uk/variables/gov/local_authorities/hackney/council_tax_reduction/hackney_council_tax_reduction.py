from policyengine_uk.model_api import *
import numpy as np
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hackney_working_age,
)


class hackney_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Hackney Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hackney.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_hackney_working_age(local_authority, country, has_pensioner)
        has_uc = benunit("universal_credit", period) > 0
        applicable_amount = where(
            has_uc,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        capital = benunit.household("savings", period)
        weekly_tariff_income = np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_step
        )
        return legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "hackney_council_tax_reduction_non_dep_deductions",
            applicable_amount=applicable_amount,
            additional_applicable_income=where(
                has_uc, 0, weekly_tariff_income * WEEKS_IN_YEAR
            ),
        )
