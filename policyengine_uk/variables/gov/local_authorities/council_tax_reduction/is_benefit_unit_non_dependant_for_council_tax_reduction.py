from policyengine_uk.model_api import *


class is_benefit_unit_non_dependant_for_council_tax_reduction(Variable):
    value_type = bool
    entity = Person
    label = "Non-dependant within the benefit unit for Council Tax Reduction"
    documentation = (
        "A member of the benefit unit who is neither the Council Tax "
        "Reduction applicant or partner (is_council_tax_reduction_applicant_or_partner) "
        "nor a child or young person: someone aged 16 or over who is not a "
        "Child Benefit qualifying young person. Such a person is outside the "
        "applicant's family but normally resides with the applicant, so is a "
        "non-dependant. Usually the applicant is the benefit unit's claimant, "
        "and this is the same set as "
        "is_benefit_unit_non_dependant_for_legacy_benefits. Where a household "
        "head who is not the benefit unit's claimant or partner applies alone "
        "(council_tax_reduction_head_applies_alone), the benefit unit's "
        "claimant and partner are the head's non-dependants. This person's own "
        "benefit awards are not modelled, so the exemptions for a "
        "non-dependant on an income-related benefit or on Universal Credit "
        "with no earned income never apply to them."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/9",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/3",
    )

    def formula(person, period, parameters):
        # SI 2012/2885 and WSI 2013/3029 reg 9(1), (2)(a), (c); SSI 2021/249
        # reg 8(2)(a)-(b); SSI 2012/319 reg 3: anyone normally residing with the
        # applicant except the applicant's own family.
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        return ~applicant_or_partner & ~child_or_young_person
