from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)


class is_uc_benefit_cap_exempt_qualifying_age(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Universal Credit benefit cap at State Pension Credit age"
    documentation = (
        "Whether the single claimant, or both joint claimants, have reached "
        "the qualifying age for State Pension Credit. SI 2014/1230 reg. 60C "
        "disapplies the cap (UC Regs 2013 reg. 79) for a qualifying claim "
        "made by such claimants. A claimant over that age does not meet the "
        "basic condition in WRA 2012 s. 4(1)(b); a couple may claim jointly "
        "where only one member is over it (UC Regs 2013 reg. 3(2)(a)), and "
        "reg. 60A waives the condition only for a qualifying claim by "
        "claimants migrated from working tax credit. So an award to such "
        "claimants is one to which reg. 60C applies. The model's own "
        "eligibility test needs a claimant under the qualifying age, so this "
        "matters only where an award is supplied as an input. A mixed-age "
        "couple's joint award is capped like any other."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60C",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60A",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # The claimants: the single claimant or each joint claimant. The other
        # member of a reg. 3(3) single claim is not a claimant.
        claimant = person("is_uc_assessed_claimant", period) & ~(
            other_member_of_single_claim(person, period)
        )
        attained = person("has_attained_state_pension_credit_qualifying_age", period)
        return benunit.any(claimant) & benunit.all(attained | ~claimant)
