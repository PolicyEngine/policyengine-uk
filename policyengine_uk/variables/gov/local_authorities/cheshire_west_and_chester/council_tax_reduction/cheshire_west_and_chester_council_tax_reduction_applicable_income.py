from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheshire West and Chester Council Tax Reduction applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-1.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.cheshire_west_and_chester.council_tax_reduction
        person = benunit.members
        earnings = benunit.sum(
            person("employment_income", period)
            + person("self_employment_income", period)
        )
        earnings_disregard = min_(
            earnings,
            (earnings > 0) * ctr.earnings_disregard.amount * WEEKS_IN_YEAR,
        )
        source_disregarded_income = benunit(
            "cheshire_west_and_chester_council_tax_reduction_source_disregarded_income",
            period,
        )
        return max_(
            0,
            benunit("council_tax_reduction_applicable_income", period)
            - earnings_disregard
            - source_disregarded_income,
        )
