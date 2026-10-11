from policyengine_uk.model_api import *


class is_council_tax_reduction_applicant_or_partner(Variable):
    value_type = bool
    entity = Person
    label = "Council Tax Reduction applicant or partner"
    documentation = (
        "Whether this person is the applicant, or the applicant's partner, "
        "for the Council Tax Reduction means test of their family. The "
        "applicant is the person liable for the council tax "
        "(council_tax_reduction_liable_person), and the means test covers the "
        "applicant's own income and their partner's. "
        "Where the family's liable person is the benefit unit's claimant or "
        "partner, this is the benefit unit's claimant and partner, whatever "
        "their ages: a partner under 18 is not liable, but their income "
        "counts. Where the liable person is a household head who is not the "
        "benefit unit's claimant or partner, it is the head alone (see "
        "council_tax_reduction_head_applies_alone). A family with no liable "
        "person cannot claim; for it this is the benefit unit's claimant and "
        "partner."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/14",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/21",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/23",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/26",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/5",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/36",
    )

    def formula(person, period, parameters):
        # SSI 2012/319 reg 21(1), SI 2012/2885 Sch 1 para 11 and the Welsh
        # and 2021 Scottish equivalents: the income and capital of the
        # applicant and of the applicant's partner.
        head_applies_alone = person.benunit(
            "council_tax_reduction_head_applies_alone", period
        )
        liable_head = person("council_tax_reduction_liable_person", period) & person(
            "is_resolved_household_head", period
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        return where(head_applies_alone, liable_head, claimant_or_partner)
