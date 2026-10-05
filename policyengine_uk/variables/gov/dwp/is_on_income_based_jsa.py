from policyengine_uk.model_api import *


class is_on_income_based_jsa(Variable):
    value_type = bool
    entity = Person
    label = "on income-based JSA"
    documentation = (
        "Whether an income-based jobseeker's allowance is payable to this "
        "person (HB Regs 2006 reg 2(3); the council tax reduction schemes use "
        "the same definition). A couple's award covers both partners, and the "
        "model treats the claimant and the partner as both on it when their "
        "award (claimant_or_partner_jsa_income) is positive. Any other member "
        "of the benefit unit, such as a non-dependent adult, claims in their "
        "own right and is on it only if they report an award themselves while "
        "the benefit unit's modelled income-based JSA is positive."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
    )

    def formula(person, period, parameters):
        couple_award = person.benunit("claimant_or_partner_jsa_income", period) > 0
        # Their own report, while the model pays income-based JSA in the
        # benefit unit (so not once it closes or a reform removes it).
        own_award = (person("jsa_income_reported", period) > 0) & (
            person.benunit("jsa_income", period) > 0
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
