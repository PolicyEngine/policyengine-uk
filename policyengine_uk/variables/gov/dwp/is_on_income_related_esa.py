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
        "Whether an income-related employment and support allowance is payable "
        'to this person (HB Regs 2006 reg 2(3A): on any day it "is payable to '
        'him"; the council tax reduction schemes use the same definition). A '
        "couple's award is paid to the claimant, not the partner: of the "
        "claimant and partner, only the payee is on it, meaning the one who "
        "reports the award, or the claimant where neither does, and only while "
        "their award (claimant_or_partner_esa_income) is positive. A member "
        "who has reached pensionable age cannot be the claimant (Welfare Reform "
        "Act 2007 s.1(3)(c)), so where the other member has not, only the "
        "other member can be the payee. Any other "
        "member of the benefit unit, such as a non-dependent adult, claims in "
        "their own right and is on it only if their own claim passes: they "
        "have not reached pensionable age (is_SP_age; s.1(3)(c)), they are not "
        "engaged in remunerative work as its claimant "
        "(esa_income_claimant_remunerative_work; Sch 1 para 6(1)(e)), and the "
        "award on their own report alone is positive, "
        "the report exceeding the tariff income from the benefit unit's "
        "capital, within the capital limit. On the formula path the claimant's "
        "or partner's claim and work never change this. The legacy "
        "benefits for this person's own award must remain open "
        "(person_legacy_benefits_closed), and the benefit unit's modelled award must "
        "be in payment: positive, or nil while esa_income_eligible fails and "
        "esa_income is not neutralised. On the formula path that nil comes only "
        "from the retained value-based override convention. Formula totals "
        "include each outside member's separately screened own award. "
        "Neutralising esa_income removes the status; a nil esa_income entered "
        "directly, or a reform that replaces it with nil, removes it only while "
        "the screen passes."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/ukpga/2007/5/section/1",
        "https://www.legislation.gov.uk/ukpga/2007/5/schedule/1/paragraph/6",
    )

    def formula(person, period, parameters):
        # WRA 2007 s.1(3)(c): a member who has reached pensionable age cannot
        # be the claimant, so the award is not payable to them.
        pensionable_age = person("is_SP_age", period)
        couple_award = (
            person.benunit("claimant_or_partner_esa_income", period) > 0
        ) & is_payee_of_couple_award(
            person, period, "esa_income_reported", can_claim=~pensionable_age
        )
        # Their own claim, on their own report, work and age alone (WRA 2007
        # s.1(3)(c): a claimant who has reached pensionable age is not entitled).
        own_award = own_report_is_paid(
            person,
            period,
            "esa_income",
            barred=person("esa_income_claimant_remunerative_work", period)
            | pensionable_age,
            capital_limit=parameters(period).gov.dwp.ESA.income.capital.limit,
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
