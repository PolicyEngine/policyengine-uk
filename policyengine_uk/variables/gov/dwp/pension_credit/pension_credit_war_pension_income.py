from policyengine_uk.model_api import *


class pension_credit_war_pension_income(Variable):
    label = "War pension income counted for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    documentation = (
        "The claimant's and partner's war disablement pensions, war widow's or "
        "widower's pensions and Armed Forces Compensation Scheme payments, each "
        "payment less the Sch. IV para. 1 disregard. afcs holds Armed Forces "
        "Compensation Scheme payments, including guaranteed income payments, "
        "and war disablement pensions; war_widows_pension holds war widow's or "
        "widower's pensions. Each of the two gets its own weekly disregard, "
        "which does not pass to the other payment or to the other member of a "
        "couple. Dependants' and other benefit-unit members' payments do not "
        "count (State Pension Credit Act 2002 s.5; reg. 14). Components that "
        "Sch. IV paras 2 to 6 and 12 disregard in full, and reg. 15(5)(a) and "
        "(ab) payments that count in full, are not separated in the data."
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
        disregard = p.war_pension_disregard * WEEKS_IN_YEAR
        counted = 0
        for payment in ["afcs", "war_widows_pension"]:
            counted += max_(person(payment, period) - disregard, 0)
        return benunit.sum(counted * person("is_claimant_or_partner", period))
