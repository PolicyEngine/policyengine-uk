from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_derby_working_age,
)


class derby_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Derby Council Tax Support"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.derby.gov.uk/media/derbycitycouncil/contentassets/documents/adviceandbenefits/counciltax/council-tax-support-scheme2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.derby.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_derby_working_age(local_authority, country, has_pensioner)
        award = legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "derby_council_tax_reduction_non_dep_deductions",
            maximum_eligible_liability_variable=(
                "derby_council_tax_reduction_maximum_eligible_liability"
            ),
        )
        annual_minimum_award = ctr.means_test.minimum_award * WEEKS_IN_YEAR
        return where(award >= annual_minimum_award, award, 0)
