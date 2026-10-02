from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
)


class is_on_income_related_esa(Variable):
    value_type = bool
    entity = Person
    label = "on income-related ESA"
    documentation = (
        "Whether an income-related employment and support allowance is "
        'payable to this person (HB Regs 2006 reg 2(3A): on any day it "is '
        'payable to him"; the council tax reduction schemes use the same '
        "definition). A couple's award is paid to the claimant, not the "
        "partner: of the claimant and partner, only the payee is on it, "
        "meaning the one who reports the award, or the claimant where neither "
        "does, and only while their award (claimant_or_partner_esa_income) "
        "is positive. Any other member of the benefit unit, such as a "
        "non-dependent adult, claims in their own right and is on it only if "
        "they report an award themselves while the benefit unit's modelled "
        "income-related ESA is positive."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
    )

    def formula(person, period, parameters):
        couple_award = (
            person.benunit("claimant_or_partner_esa_income", period) > 0
        ) & (is_payee_of_couple_award(person, period, "esa_income_reported"))
        # Their own report, while the model pays income-related ESA in the
        # benefit unit (so not once a reform removes or zeroes it).
        own_award = (person("esa_income_reported", period) > 0) & (
            person.benunit("esa_income", period) > 0
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
