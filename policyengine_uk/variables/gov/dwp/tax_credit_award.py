from policyengine_uk.model_api import *


class tax_credit_award(Variable):
    value_type = float
    entity = Person
    label = "tax credit award"
    documentation = (
        "The award of Child Tax Credit and Working Tax Credit payable to this "
        "person. A couple claims tax credits jointly (TCA 2002 s.3(3)(a)), so "
        "for the claimant and the partner it is their benefit unit's award "
        "(tax_credits). Any other member of the benefit unit claims in their "
        "own right, so for them it is the award they report themselves while "
        "tax credits are in payment."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/21/section/3"

    def formula(person, period, parameters):
        couple_award = person.benunit("tax_credits", period)
        own_award = parameters(period).gov.dwp.tax_credits.active * add(
            person,
            period,
            ["child_tax_credit_reported", "working_tax_credit_reported"],
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
