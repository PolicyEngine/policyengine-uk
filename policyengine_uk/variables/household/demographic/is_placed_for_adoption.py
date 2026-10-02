from policyengine_uk.model_api import *


class is_placed_for_adoption(Variable):
    value_type = bool
    entity = Person
    label = "placed for adoption"
    documentation = (
        "Whether this child is placed for adoption with the claimant or "
        "partner of their benefit unit (an adopter), or placed with them "
        "prior to adoption. Put the child in the adopter's benefit unit and "
        "leave is_looked_after_by_local_authority false: under Universal "
        "Credit the adopter is responsible for the child (UC Regs 2013 reg "
        "4A(1)(c)) and satisfies the foster parent condition for an "
        "additional bedroom (Sch 4 para 12(4)(b)), and Pension Credit treats "
        "them as the adopter's responsibility too (SPC Regs 2002 Sch IIA "
        "para 4(3)(c)). Under Housing Benefit, the other legacy schemes and "
        "council tax reduction the child is not a member of the claimant's "
        "household (HB Regs 2006 reg 21(3)(b)-(c); CTR (England) prescribed "
        "requirements reg 8(2)(b)-(c)), and no one is responsible for them "
        "for Tax-Free Childcare (Childcare Payments (Eligibility) Regs 2015 "
        "reg 4(2)(d)). Child Tax Credit excludes a child placed for adoption "
        "only while the local authority pays for their accommodation or "
        "maintenance (CTC Regs 2002 reg 3, rule 4 case B), which is not "
        "modelled."
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
    )
