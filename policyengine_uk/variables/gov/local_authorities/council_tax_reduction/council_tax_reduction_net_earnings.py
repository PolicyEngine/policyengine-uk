from policyengine_uk.model_api import *


class council_tax_reduction_net_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction net earnings"
    documentation = (
        "Net earnings of the Council Tax Reduction applicant and partner "
        "(is_council_tax_reduction_applicant_or_partner), from which the "
        "pensioner earnings disregards are taken. Each person's net earnings "
        "are those of the Housing Benefit means test "
        "(housing_benefit_person_net_earnings), whose deductions the "
        "pensioner schemes share. Where the applicant is the benefit unit's "
        "claimant this equals housing_benefit_net_earnings; where the "
        "household head applies alone it is the head's own net earnings."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/19",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/33",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        net_earnings = person("housing_benefit_person_net_earnings", period)
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        return benunit.sum(net_earnings * applicant_or_partner)
