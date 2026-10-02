from policyengine_uk.model_api import *


class is_child_who_cannot_share_bedroom(Variable):
    value_type = bool
    entity = Person
    label = "Child who cannot share a bedroom (LHA size criteria)"
    documentation = (
        "A child under 16 who receives the care component of Disability "
        "Living Allowance at the middle or highest rate and is not reasonably "
        "able to share a bedroom with another child because of their "
        "disability (cannot_reasonably_share_bedroom_due_to_disability). "
        "This is the child in the Universal Credit disabled child condition "
        "and the Housing Benefit 'child who cannot share a bedroom', in force "
        "from 4 December 2013. The law also accepts the care component of "
        "child disability payment (Scotland), which the model counts only "
        "where the data record it as Disability Living Allowance. Whether "
        "the child would otherwise be expected to share is decided in the "
        "size criteria (see LHA_cannot_share_bedrooms and "
        "housing_benefit_LHA_cannot_share_bedrooms)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/2828/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.LHA.cannot_share_bedroom.child
        # UC Regs 2013 reg 2 and HB Regs 2006 reg 2(1): a child is a person
        # under 16.
        child = person("age", period) < 16
        # UC Sch 4 para 12(6)(a); HB reg 2(1), "child who cannot share a
        # bedroom", (a).
        qualifying_benefit = add(person, period, p.benefits) > 0
        # Para 12(6)(b); reg 2(1), (b).
        cannot_share = person(
            "cannot_reasonably_share_bedroom_due_to_disability", period
        )
        return p.in_effect & child & qualifying_benefit & cannot_share
