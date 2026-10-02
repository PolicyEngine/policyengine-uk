from policyengine_uk.model_api import *


class council_tax_reduction_head_applies_alone(Variable):
    value_type = bool
    entity = BenUnit
    label = "Household head applies for Council Tax Reduction alone"
    documentation = (
        "Whether this family's Council Tax Reduction applicant is its "
        "household head alone, because the head is treated as liable for the "
        "council tax but is not the benefit unit's claimant or partner. An "
        "example is a grandmother who heads the household and shares a benefit "
        "unit with a young couple and their baby: the couple are the benefit "
        "unit's claimant and partner, but she is the person liable for the "
        "council tax. The applicant's means test then covers the head's own "
        "income and circumstances, as a single person with no partner or "
        "children, since the model cannot tell whether any other member is "
        "the head's partner or child. The benefit unit's means-tested "
        "benefits (such as Universal Credit, Income Support and Child Benefit) "
        "belong to its claimant and partner, not to the head."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/14",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/21",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/36",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        liable_head = person("council_tax_reduction_liable_person", period) & person(
            "council_tax_reduction_household_head", period
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        return benunit.any(liable_head & ~claimant_or_partner)
