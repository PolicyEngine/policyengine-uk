from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
    own_report_is_paid,
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
        "the award on their own report alone is positive: the report exceeds "
        "the tariff income from the benefit unit's capital, within the "
        "capital limit, while the benefit unit's modelled award is positive."
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
        # The award on their own report alone, never another member's.
        own_award = own_report_is_paid(person, period, "esa_income")
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
