from policyengine_uk.model_api import *


class pension_credit_war_pension_income(Variable):
    label = "War pension income counted for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    documentation = (
        "The claimant's and partner's war disablement pensions, war widow's or "
        "widower's pensions and Armed Forces Compensation Scheme payments "
        "(afcs, which holds guaranteed income payments and war disablement "
        "pensions), less the Sch. IV para. 1 disregard. One weekly disregard "
        "applies to each person's payments together, and the claimant and "
        "partner each have their own (reg. 14). Dependants' and other "
        "benefit-unit members' payments do not count. Components that Sch. IV "
        "paras 2 to 6 and 12 disregard in full, and reg. 15(5)(a) and (ab) "
        "payments that count in full, are not separated in the data."
    )
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/14",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV/paragraph/1",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.income
        person = benunit.members
        payments = add(person, period, ["afcs", "war_widows_pension"])
        disregard = p.war_pension_disregard * WEEKS_IN_YEAR
        counted = max_(payments - disregard, 0)
        return benunit.sum(counted * person("is_claimant_or_partner", period))
