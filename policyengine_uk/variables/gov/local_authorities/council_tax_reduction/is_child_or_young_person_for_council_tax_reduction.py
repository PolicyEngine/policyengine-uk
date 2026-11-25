from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class is_child_or_young_person_for_council_tax_reduction(Variable):
    """Child or young person in the applicant's family for Council Tax Reduction.

    Every scheme defines a child as a person under 16. They differ on the
    young person:

    - Scotland's working-age scheme, from 1 April 2022, uses the Universal
      Credit child and the qualifying young person of UC Regs 2013 reg. 5
      (Council Tax Reduction (Scotland) Regulations 2021 reg. 6(1)). The
      Secretary of State has reg. 5(5) apply as if it also named an existing
      benefit, for a person entitled to one (SI 2014/1230 reg. 28(b)). Under
      Interpretation Act 1978 s. 20(2), which s. 23(1) applies to subordinate
      legislation, the model reads the Scottish Ministers' reference to reg. 5
      as including that modification. So a person who is entitled to and
      receives Income Support, Housing Benefit, a tax credit, income-related
      ESA or income-based JSA is not a young person here, and the formula
      reads is_child_or_qualifying_young_person_for_universal_credit, which
      applies is_qualifying_young_person_for_universal_credit. The law is
      unsettled on whether the Scottish reference carries reg. 28(b). The
      applicant is responsible for a child or young person who normally lives
      with them, never for one they live with as a couple, and no one is
      responsible for one placed with a foster carer (reg. 7).
    - England, Wales and Scotland's pension-age scheme use the Child Benefit
      qualifying young person (SI 2012/2885 reg. 2; WSI 2013/3029 reg. 2; SSI
      2012/319 reg. 4), as Housing Benefit does.

    The scheme follows the family's own pensioner status
    (council_tax_reduction_pensioner).

    Both branches leave out every child or young person looked after by a
    local authority, as the Universal Credit and legacy flags do. That is
    broader than Scotland's working-age rule, which names only a child or
    young person placed with a foster carer under the Looked After Children
    (Scotland) Regulations 2009 (reg. 7(8)). The Child Benefit branch also
    leaves out a child placed for adoption with the applicant or partner
    (SI 2012/2885 reg. 8(2); SI 2012/2886 Sch para. 8(2); WSI 2013/3029
    reg. 8(2); SSI 2012/319 reg. 11(2)). The Universal Credit branch keeps
    them, since the Universal Credit flag has no adoption rule and, of
    children, leaves out only those looked after (is_looked_after_child).
    So on Scotland's working-age scheme from 1 April 2022 the applicant is
    responsible for a child placed for adoption who normally lives with
    them (reg. 7(2)).
    Before 1 April 2022 Scotland's working-age scheme follows the Child
    Benefit branch.
    """

    value_type = bool
    entity = Person
    label = "Child or young person for Council Tax Reduction"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/ukpga/1978/30/section/20",
        "https://www.legislation.gov.uk/ukpga/1978/30/section/23",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/6",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/7",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/4",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/2",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.working_age
        scottish_working_age = (
            (person.household("country", period) == Country.SCOTLAND)
            & ~person.benunit("council_tax_reduction_pensioner", period)
            & p.young_person_follows_universal_credit
        )
        # SSI 2021/249 regs 4, 6 and 7: a child, a person under 16 (reg. 4(1)), or a
        # qualifying young person under UC Regs reg. 5 (reg. 6(1)). The model reads
        # that reference as including SI 2014/1230 reg. 28(b)'s modification of reg.
        # 5(5) (Interpretation Act 1978 s. 20(2), applied by s. 23(1)), so it reads
        # the Universal Credit flag, which applies reg. 28. That flag already leaves
        # out a child looked after by a local authority, which only a person under 18
        # can be (is_looked_after_child).
        universal_credit = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        ) & ~person("is_claimant_or_partner", period)
        child_benefit = person("is_child_or_young_person_for_legacy_benefits", period)
        return where(scottish_working_age, universal_credit, child_benefit)
