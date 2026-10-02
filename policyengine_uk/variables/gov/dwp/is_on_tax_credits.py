from policyengine_uk.model_api import *


class is_on_tax_credits(Variable):
    value_type = bool
    entity = Person
    label = "on tax credits"
    documentation = (
        "Whether an award of Child Tax Credit or Working Tax Credit is "
        "payable to this person. A couple claims tax credits jointly (TCA "
        "2002 s.3(3)(a)), so the claimant and the partner are both on them "
        "when their benefit unit's award (tax_credits) is positive. An award "
        "below the minimum (£26 a year) is not paid (SI 2002/2008 reg 9), so "
        "a positive award is one of at least £26, the test the 2024-25 winter "
        "fuel and pension age winter heating payments set. Any other member "
        "of the benefit unit claims in their own right and is on them only if "
        "they report awards of at least the minimum themselves while tax "
        "credits are in payment."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/uksi/2002/2008/regulation/9",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits
        couple_award = person.benunit("tax_credits", period) > 0
        own_award = add(
            person,
            period,
            ["child_tax_credit_reported", "working_tax_credit_reported"],
        )
        own_award_payable = p.active & (own_award >= p.min_benefit)
        return where(
            person("is_claimant_or_partner", period),
            couple_award,
            own_award_payable,
        )
