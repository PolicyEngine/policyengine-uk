from policyengine_uk.model_api import *


class is_uc_work_allowance_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family receives a Universal Credit Work Allowance"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/22"

    def formula(benunit, period, parameters):
        person = benunit.members
        # UC Regs 2013 reg 22(1)(b): responsibility for a child or qualifying
        # young person, or limited capability for work.
        has_LCW = benunit.any(person("uc_limited_capability_for_work", period))
        has_children = benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
            period,
        )
        return has_LCW | has_children
