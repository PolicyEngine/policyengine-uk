from policyengine_uk.model_api import *


class is_benefit_unit_non_dependant_for_legacy_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Non-dependant within the benefit unit for Housing Benefit and Council Tax Reduction"
    documentation = (
        "A member of the benefit unit who is neither the claimant or partner "
        "nor a child or young person: someone aged 16 or over who is not a "
        "Child Benefit qualifying young person. The benefit unit follows the "
        "survey's family, which can include an adult child or a 16 to 19 year "
        "old who is not a qualifying young person. Under the Housing Benefit "
        "and Council Tax Reduction schemes such a person is not in the "
        "claimant's family (SSCBA 1992 s.137(1), with young person defined "
        "by Child Benefit) but normally resides with the claimant, so is a "
        "non-dependant. A child or young person is either in the family or, "
        "if placed with the claimant by a local authority, excluded from "
        "being a non-dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/9",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/3",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/137",
    )

    def formula(person, period, parameters):
        # HB Regs 2006 and HB (SPC) Regs 2006 reg 3(2)(a), (c) with regs 19
        # and 21(3); SI 2012/2885 and WSI 2013/3029 reg 9(2)(a), (c); SSI
        # 2021/249 reg 8(2)(a)-(b); SSI 2012/319 reg 3. A Child Benefit child
        # is under 16.
        claimant_or_partner = person("is_claimant_or_partner", period)
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        return ~claimant_or_partner & ~child_or_young_person
