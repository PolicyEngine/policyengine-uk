from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "South Gloucestershire Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://beta.southglos.gov.uk/apply-for-council-tax-reduction/",
        "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf",
    ]

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_gloucestershire.council_tax_reduction
        local_scheme = benunit(
            "south_gloucestershire_council_tax_reduction_is_local_scheme", period
        )
        support_rate = benunit(
            "south_gloucestershire_council_tax_reduction_support_rate", period
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "south_gloucestershire_council_tax_reduction_non_dep_deductions",
            period,
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        capital = benunit(
            "south_gloucestershire_council_tax_reduction_assessable_capital",
            period,
        )
        capital_eligible = capital <= ctr.means_test.capital_limit
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
