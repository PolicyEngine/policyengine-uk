from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.child_element.is_qualifying_young_person_for_universal_credit import (
    qualifying_young_person,
)


class is_qualifying_young_person_for_uc_education(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for the Universal Credit education condition"
    documentation = (
        "Whether this person counts as a qualifying young person for the "
        "Universal Credit condition that a claimant is not receiving "
        "education. Under the Universal Credit (Transitional Provisions) "
        "Regulations 2014 reg. 28, a person entitled to an existing benefit "
        "doesn't count as a qualifying young person, and the Secretary of "
        "State lists the existing benefits in reg. 2(1): income-based "
        "Jobseeker's Allowance, income-related Employment and Support "
        "Allowance, Income Support, Housing Benefit, Child Tax Credit and "
        "Working Tax Credit. It reads "
        "is_qualifying_young_person_for_universal_credit, which applies reg. "
        "28, but for a claimant or partner it reads the status on the first "
        "day of their Universal Credit award. A claim ends a tax credit award "
        "the day before the award starts (reg. 8(2)(a)), but a Housing "
        "Benefit award only two weeks after (reg. 8(2A)), and the model's "
        "esa_income_report_closed describes the same run-on for "
        "income-related ESA. The Secretary of State inserted reg. 8(2A) from "
        "11 April 2018 (SI 2018/65), and SI 2019/1152 reg. 5 gives the "
        "income-related ESA run-on only to claims made from 22 July 2020; "
        "the annual model applies both run-ons in earlier years too. So the "
        "Secretary of State still excludes a "
        "claimant on such an award that day (reg. 28), and once they receive "
        "Universal Credit, as a person receiving it (Universal Credit "
        "Regulations 2013 reg. 5(5)), which the model's reg. 5 test reads "
        "only from reported Universal Credit. The formula therefore leaves "
        "out the Housing Benefit and income-related ESA claim limbs that "
        "is_qualifying_young_person_for_universal_credit follows, and keeps "
        "the Child Tax Credit one, the year gates and the legacy closures. A "
        "claimant whose Universal Credit comes to nil receives none, so after "
        "the run-on the law counts them as a qualifying young person again; "
        "the annual model keeps them outside the definition all year. A "
        "person outside the definition under reg. 28 takes the ordinary "
        "route under the Universal Credit Regulations 2013 reg. 12(2). For "
        "the reg. 60(1) protection the model reads the status on the "
        "migration day instead (is_qualifying_young_person_on_uc_migration_day). "
        "In Northern Ireland the decision maker applies the same rule under "
        "reg. 29 of the Universal Credit (Transitional Provisions) Regulations "
        "(Northern Ireland) 2016, with reg. 6 of the Universal Credit "
        "Regulations (Northern Ireland) 2016 in place of the Universal Credit "
        "Regulations 2013 reg. 5. SR 2016/226 reg. 6 ends awards on the same "
        "days as reg. 8, and SR 2019/152 reg. 4 gives the income-related ESA "
        "run-on to claims made from 22 July 2020, with one difference: a claim "
        "ends a rate rebate the day before the award starts (reg. 6(2)), and "
        "only a rent rebate or allowance runs on (reg. 6(2A)). The report "
        "doesn't show the form. A rent rebate or allowance needs rent or a "
        "similar payment (Housing Benefit Regulations (Northern Ireland) 2006 "
        "reg. 13(1)), so the formula reads a report in a family that doesn't "
        "rent as a rate rebate (reg. 12), and a claimant with no other "
        "existing benefit counts as a qualifying young person on the first "
        "day. The model can't see someone who owns a caravan or houseboat and "
        "pays site or mooring charges (reg. 13(1)(f) and (g)), so it reads "
        "their rent allowance as a rate rebate."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2013/983/article/4",
        "https://www.legislation.gov.uk/uksi/2019/1152/regulation/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/6",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/6",
        "https://www.legislation.gov.uk/nisr/2017/190/article/6",
        "https://www.legislation.gov.uk/nisr/2019/152/regulation/4",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/12",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/13",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/12",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/13",
    )

    def formula(person, period, parameters):
        # Those whom the Housing Benefit and income-related ESA claim limbs
        # readmit: on the first day of their award the Secretary of State
        # still excludes them through reg. 28, and once they receive
        # Universal Credit through reg. 5(5). Removing only them keeps any
        # input or reform that sets the predicate.
        readmitted = qualifying_young_person(
            person, period, parameters
        ) & ~qualifying_young_person(person, period, parameters, at_claim_start=True)
        return (
            person("is_qualifying_young_person_for_universal_credit", period)
            & ~readmitted
        )
