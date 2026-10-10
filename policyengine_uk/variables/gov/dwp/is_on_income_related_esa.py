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
        "their own claim passes: they are not engaged in remunerative work as "
        "its claimant (esa_income_claimant_remunerative_work; Welfare Reform "
        "Act 2007 Sch 1 para 6(1)(e)), and the award on their own report alone "
        "is positive, the report exceeding the tariff income from the benefit "
        "unit's capital, within the capital limit. On the formula path the "
        "claimant's or partner's claim and work never change this. The "
        "benefit unit's "
        "modelled award must also be in payment: positive, or nil only "
        "because the claimant's or partner's own claim fails "
        "esa_income_eligible, so neutralising esa_income removes the status."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/ukpga/2007/5/schedule/1/paragraph/6",
    )

    def formula(person, period, parameters):
        couple_award = (
            person.benunit("claimant_or_partner_esa_income", period) > 0
        ) & (is_payee_of_couple_award(person, period, "esa_income_reported"))
        # Their own claim, on their own report and their own work alone.
        own_award = own_report_is_paid(
            person,
            period,
            "esa_income",
            works=person("esa_income_claimant_remunerative_work", period),
            capital_limit=parameters(period).gov.dwp.ESA.income.capital.limit,
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
