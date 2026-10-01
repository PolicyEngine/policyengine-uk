from policyengine_uk.model_api import *


class is_on_income_support(Variable):
    value_type = bool
    entity = Person
    label = "on Income Support"
    documentation = (
        'Whether this person is in receipt of Income Support ("person on '
        'income support", HB Regs 2006 reg 2(1); the council tax reduction '
        "schemes use the same definition). Income Support is calculated for "
        "the claimant's family and needs the claimant's or partner's own "
        "award (income_support_eligible). A couple's award covers both "
        "partners, and the model treats the claimant and the partner as both "
        "on it when it is positive. Any other member of the benefit unit, "
        "such as a non-dependent adult, claims in their own right and is on "
        "it only if they report an award themselves while Income Support is "
        "in payment."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
    )

    def formula(person, period, parameters):
        active = parameters(period).gov.dwp.income_support.active
        couple_award = person.benunit("income_support", period) > 0
        own_award = active & (person("income_support_reported", period) > 0)
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
