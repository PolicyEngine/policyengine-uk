from policyengine_uk.model_api import *


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
        "Working Tax Credit. It equals "
        "is_qualifying_young_person_for_universal_credit, which applies reg. "
        "28. A person outside the definition under reg. 28 takes the ordinary "
        "route under the Universal Credit Regulations 2013 reg. 12(2). For "
        "the reg. 60(1) protection the model reads the status on the "
        "migration day instead (is_qualifying_young_person_on_uc_migration_day). "
        "In Northern Ireland the decision maker applies the same rule under "
        "reg. 29 of the Universal Credit (Transitional Provisions) Regulations "
        "(Northern Ireland) 2016, with reg. 6 of the Universal Credit "
        "Regulations (Northern Ireland) 2016 in place of the Universal Credit "
        "Regulations 2013 reg. 5."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/6",
    )

    def formula(person, period, parameters):
        return person("is_qualifying_young_person_for_universal_credit", period)
