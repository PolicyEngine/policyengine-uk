from policyengine_uk.model_api import *


class is_placed_for_adoption(Variable):
    value_type = bool
    entity = Person
    label = "placed for adoption"
    documentation = (
        "Whether this child is placed for adoption with the claimant or "
        "partner of their benefit unit under the Adoption and Children Act "
        "2002 or the Adoption and Children (Scotland) Act 2007. Put the child "
        "in the adopter's benefit unit and leave "
        "is_looked_after_by_local_authority false. A fostering-for-adoption "
        "placement (Children Act 1989 s.22C(9A)-(9B)) is a foster placement: "
        "flag that child as looked after instead. Universal Credit treats the "
        "adopter as responsible for the child (UC Regs 2013 reg 4A(1)(c)), "
        "and the adopter satisfies the foster parent condition for an "
        "additional bedroom (Sch 4 para 12(4)(b)). That condition's "
        "definition of adopter (reg 89(3)(a)) excludes a foster parent or "
        "close relative of the child, which the model does not check. "
        "Pension Credit also treats the adopter as responsible (SPC Regs 2002 "
        "Sch IIA para 4(3)(c)). Under Housing Benefit, Income Support, "
        "income-based Jobseeker's Allowance, income-related Employment and "
        "Support Allowance and the English pensioner, Welsh and Scottish "
        "pension-age council tax reduction schemes, the child is not a "
        "member of the claimant's household; a single claimant or lone "
        "parent with such a child is in an Income Support prescribed "
        "category (IS Regs 1987 Sch 1B para 2A). Tax-Free Childcare does not "
        "count them (Childcare Payments (Eligibility) Regs 2015 reg "
        "4(2)(d)). Child Tax Credit excludes them only while the local "
        "authority pays for their keep (CTC Regs 2002 reg 3, rule 4 case B), "
        "which is not modelled. Scottish working-age council tax reduction "
        "excludes only foster placements (SSI 2021/249 reg 7(8)), so the "
        "child should count there; the model's shared legacy household test "
        "leaves them out."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4A",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/8",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/7",
    )
