from policyengine_uk.model_api import *


class in_specified_or_temporary_accommodation(Variable):
    value_type = bool
    entity = BenUnit
    label = "In specified or temporary accommodation for Housing Benefit"
    documentation = (
        "Whether this family's housing falls within the statutory specified "
        "or temporary accommodation definitions for Housing Benefit. GB "
        "Universal Credit (Transitional Provisions) Regulations 2014 reg "
        "6A(2), with the definitions in reg 2, refers to Universal Credit "
        "Regulations 2013 Schedule 1 paragraphs 3A(2)-(5) and 3B. The NI "
        "equivalents are Transitional Provisions Regulations 2016 regs 2 "
        "and 4A(2), and Universal Credit Regulations 2016 Schedule 1 "
        "paragraphs 4(2)-(5) and 4A. This is a supplied status, not inferred "
        "from tenure or a generic supported-housing label. The working-age "
        "Housing Benefit earnings disregard for specified or temporary "
        "accommodation (SI 2006/213 Sch 4 para 18; NI SR 2006/405 Sch 5 para "
        "18), which refers to the same paragraphs, reads it. Housing Benefit "
        "eligibility reads it for new claims and for awards that continue "
        "after a Universal Credit claim or DWP's move off legacy benefits "
        "(SI 2014/1230 regs 6A(2), 8(3) and 46(2); NI: SR 2016/226 regs "
        "4A(2), 6(3) and 47(2)), and the Universal Credit housing costs "
        "element is nil for it (UC Regs 2013 Sch 1 paras 3(h) and 3(i); NI: "
        "SR 2016/216 Sch 1 paras 3(e) and 3(ea)). Universal Credit pays "
        "nothing towards this rent, so a family gets help with it only "
        "through Housing Benefit. A hand-entered family that reports another "
        "of the seven means-tested benefits and no Housing Benefit claims "
        "only what it reports (would_claim_housing_benefit), and gets none; "
        "to model the claim, set housing_benefit_reported or "
        "would_claim_housing_benefit. "
        "It defaults to False when absent from household or dataset inputs."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A/2",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/3A",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/3B",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/4A/2",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/2",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/4",
        "https://www.legislation.gov.uk/nisr/2016/216/schedule/1/paragraph/4A",
    )
