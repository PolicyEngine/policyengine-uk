from policyengine_uk.model_api import *


class has_own_esa_award(Variable):
    value_type = bool
    entity = Person
    label = "has an ESA award of their own"
    documentation = (
        "Whether this person claims an employment and support allowance "
        "themselves: they report contributory ESA or an income-related award. "
        "When the family's income-related award is entered directly "
        "(esa_income) rather than reported, it is attributed to one claimant: "
        "the claimant or partner who heads the benefit unit, or else the "
        "eldest of them. The award's support component "
        "(esa_includes_support_component) and the work capability assessment "
        "behind it belong to this person."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2007/5/section/2",
        "https://www.legislation.gov.uk/ukpga/2007/5/section/4",
    )

    def formula(person, period, parameters):
        income_related = person("esa_income_reported", period)
        own_report = (person("esa_contrib", period) > 0) | (income_related > 0)
        claimant = person("is_claimant_or_partner", period)
        reported_by_couple = person.benunit.sum(income_related * claimant) > 0
        entered_for_couple = (
            person.benunit("claimant_or_partner_esa_income", period) > 0
        ) & ~reported_by_couple
        head_first = person("is_benunit_head", period) * 1_000 + person("age", period)
        attributed = claimant & (
            person.get_rank(person.benunit, -head_first, condition=claimant) == 0
        )
        return own_report | (entered_for_couple & attributed)
