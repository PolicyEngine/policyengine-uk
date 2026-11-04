from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.legacy_benefits_home_letting_income import (
    home_letting_income,
)


class council_tax_reduction_home_letting_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Rent from letting part of the home counted for Council Tax Reduction"
    documentation = (
        "Rent the Council Tax Reduction applicant and any partner "
        "(is_council_tax_reduction_applicant_or_partner) receive for letting "
        "part of the home they live in (sublet_income), after the weekly "
        "sub-tenant disregard for one occupier. Where the household head "
        "applies alone, the head is the applicant, so the head's own rent "
        "counts and the benefit unit's claimant's and partner's does not. The "
        "pension-age disregard applies where the applicant falls under the "
        "pension-age scheme (council_tax_reduction_pensioner). "
        "council_tax_reduction_applicable_income decides on which routes it "
        "counts."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/10",
    ]

    def formula(benunit, period, parameters):
        applicant_or_partner = benunit.members(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        return home_letting_income(
            benunit, period, parameters, applicant_or_partner, pensioner
        )
