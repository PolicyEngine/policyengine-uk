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
        "Working Tax Credit. It applies reg. 28 as "
        "is_qualifying_young_person_for_universal_credit does, except for a "
        "claimant or partner whose own income-related ESA, Housing Benefit or "
        "Child Tax Credit award the family's Universal Credit claim ends. "
        "The Secretary of State excludes a claimant while they hold an "
        "existing award (reg. 28), and one who receives Universal Credit "
        "(Universal Credit Regulations 2013 reg. 5(5)), which the model's "
        "reg. 5 test reads only from reported Universal Credit. So for such a "
        "claimant the formula reads reg. 28 against the awards they held when "
        "they claimed, and leaves out the claim limbs that "
        "is_qualifying_young_person_for_universal_credit follows. A person "
        "outside the definition under reg. 28 takes the ordinary "
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
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/6",
    )

    def formula(person, period, parameters):
        # The Secretary of State keeps such a claimant outside the
        # definition: through reg. 28 while the award their claim ends
        # runs, and through reg. 5(5) once they receive Universal Credit.
        return qualifying_young_person(person, period, parameters, claim_limbs=False)
