from policyengine_uk.model_api import *


class war_widows_pension(Variable):
    value_type = float
    entity = Person
    label = "War Widow's or Widower's Pension"
    documentation = (
        "A war widow's or widower's pension as defined in State Pension Credit "
        "Act 2002 s.17(1): a widow's, widower's or surviving civil partner's "
        "pension or allowance granted in respect of a death due to service or "
        "war injury and payable under an enactment named in the definition of "
        "war disablement pension, or granted under a scheme in s.641(1)(e) or "
        "(f) of the Income Tax (Earnings and Pensions) Act 2003. This is the "
        "gross payment. Amounts wholly disregarded by "
        "State Pension Credit Regulations 2002 Sch. IV paras 2 to 6 and 12 "
        "(for example a supplementary pension under article 23(2) of the "
        "Service Pensions Order 2006) are not separated. Family Resources "
        "Survey benefit code 9 belongs here. Microcosm separates it into "
        "war_widows_pension_reported (microcosm#1333); the Enhanced FRS and "
        "older Microcosm releases can still include it in bsp_reported "
        "(policyengine-uk-data#578)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/17",
        "https://www.legislation.gov.uk/ukpga/2003/1/section/639",
    )

    adds = ["war_widows_pension_reported"]
