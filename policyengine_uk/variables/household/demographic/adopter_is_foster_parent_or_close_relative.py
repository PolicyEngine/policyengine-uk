from policyengine_uk.model_api import *


class adopter_is_foster_parent_or_close_relative(Variable):
    value_type = bool
    entity = Person
    label = "adopter is a foster parent or close relative of the child"
    documentation = (
        "Whether the person with whom this child is placed for adoption is "
        "a foster parent or close relative of the child. Universal Credit's "
        "'adopter' (UC Regs 2013 reg 2, taking the meaning in reg 89(3)(a)) "
        "excludes such a person, so they do not meet the foster parent "
        "condition through the adoption placement (Sch 4 para 12(4)(b)), "
        "nor the shared accommodation rate exception that follows it (para "
        "29(9A)). A close relative (reg 2) is a parent, parent-in-law, son, "
        "son-in-law, daughter, daughter-in-law, step-parent, step-son, "
        "step-daughter, brother or sister, or the other member of a couple "
        "with any of them. The adopter remains responsible for the child "
        "(reg 4A(1)(c)), and Housing Benefit's placement rule (HB Regs 2006 "
        "reg 21(3)) and qualifying parent or carer carry no such words, so "
        "neither changes. A foster parent keeps the foster parent condition "
        "as a foster parent (para 12(4)(a), (5)): flag their placements or "
        "set is_approved_foster_parent_without_placement. Set this on the "
        "child; it has no effect unless is_placed_for_adoption is true."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/89",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
    )
