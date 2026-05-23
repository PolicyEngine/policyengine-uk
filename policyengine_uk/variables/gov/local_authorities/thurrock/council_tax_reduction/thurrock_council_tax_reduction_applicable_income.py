from policyengine_uk.model_api import *


class thurrock_council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Thurrock Council Tax Reduction applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://thurrock.moderngov.co.uk/documents/s51034/Enc.%201%20for%20Local%20Council%20Tax%20Support%20Scheme%202026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.thurrock.council_tax_reduction
        person = benunit.members
        earnings = benunit.sum(
            person("employment_income", period)
            + person("self_employment_income", period)
        )
        earnings_disregard = min_(
            earnings,
            (earnings > 0) * ctr.earnings_disregard.amount * WEEKS_IN_YEAR,
        )
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        source_disregarded_income = benunit(
            "thurrock_council_tax_reduction_source_disregarded_income", period
        )
        return max_(
            0,
            applicable_income - earnings_disregard - source_disregarded_income,
        )
