from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._legacy_award_payee import (
    is_payee_of_couple_award,
    own_report_is_paid,
)


class is_on_income_based_jsa(Variable):
    value_type = bool
    entity = Person
    label = "on income-based JSA"
    documentation = (
        "Whether an income-based jobseeker's allowance is payable to this "
        'person (HB Regs 2006 reg 2(3): on any day it "is payable to him"; '
        "the council tax reduction schemes use the same definition). A "
        "couple's award is paid to the claimant, not the partner: of the "
        "claimant and partner, only the payee is on it, meaning the one who "
        "reports the award, or the claimant where neither does, and only "
        "while their award (claimant_or_partner_jsa_income) is positive. The "
        "model has no joint-claim JSA input. Any other member of the benefit "
        "unit, such as a non-dependent adult, claims in their own right and "
        "is on it only if their own claim passes: they do not work 16 hours "
        "a week or more (jsa_remunerative_work_hours; Jobseekers Act 1995 "
        "s.1(2)(e), JSA Regs 1996 reg 51(1)(a)), and the award on their own "
        "report alone is positive, the report exceeding the tariff income "
        "from the benefit unit's capital, within the capital limit. On the "
        "formula path the claimant's or partner's claim and work never change "
        "this. Income-"
        "based JSA must be open (gov.dwp.JSA.income.active), and the benefit "
        "unit's modelled award in payment: positive, or nil only because the "
        "claimant's or partner's own claim fails jsa_income_eligible, so "
        "neutralising jsa_income removes the status."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
        "https://www.legislation.gov.uk/ukpga/1995/18/section/1",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/51",
    )

    def formula(person, period, parameters):
        couple_award = (
            person.benunit("claimant_or_partner_jsa_income", period) > 0
        ) & (is_payee_of_couple_award(person, period, "jsa_income_reported"))
        # Their own claim, on their own report and their own work alone.
        JSA = parameters(period).gov.dwp.JSA
        hours = person("jsa_remunerative_work_hours", period)
        own_award = JSA.income.active & own_report_is_paid(
            person,
            period,
            "jsa_income",
            works=hours >= JSA.remunerative_work.claimant_hours,
            capital_limit=JSA.income.capital.limit,
        )
        return where(person("is_claimant_or_partner", period), couple_award, own_award)
