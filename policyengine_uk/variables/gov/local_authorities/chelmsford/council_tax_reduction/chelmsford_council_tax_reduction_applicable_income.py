from policyengine_uk.model_api import *


class chelmsford_council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Chelmsford Local Council Tax Support applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.chelmsford.gov.uk/media/kmml3jha/chelmsford-s13a-scheme-202526.pdf?alId=1227933"

    def formula(benunit, period, parameters):
        weekly_disregard = benunit(
            "chelmsford_council_tax_reduction_earnings_disregard", period
        )
        person = benunit.members
        earnings = benunit.sum(
            person("employment_income", period)
            + person("self_employment_income", period)
        )
        earnings_disregard = min_(
            earnings,
            (earnings > 0) * weekly_disregard * WEEKS_IN_YEAR,
        )
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        source_disregarded_income = benunit(
            "chelmsford_council_tax_reduction_source_disregarded_income", period
        )
        return max_(
            0,
            applicable_income - earnings_disregard - source_disregarded_income,
        )
