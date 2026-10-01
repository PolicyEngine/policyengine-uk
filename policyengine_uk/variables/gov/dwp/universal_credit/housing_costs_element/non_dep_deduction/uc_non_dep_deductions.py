from policyengine_uk.model_api import *


class uc_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit non-dependent deductions"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/13",
    )

    def formula(benunit, period, parameters):
        # A housing cost contribution is deducted for each non-dependant in
        # the renter's extended benefit unit (UC Regs 2013 Sch 4 para 13).
        # Non-dependants live outside the household head's family and are
        # not liable for rent, and only the household head's family has them
        # (para 9(2)(d)-(f)): a sharer, boarder or lodger has none from the
        # household head's family.
        person = benunit.members
        deductions = person("uc_individual_non_dep_deduction", period) * person(
            "is_non_dependant_of_household_head", period
        )
        head_family = benunit.any(person("is_household_head", period))
        return head_family * benunit.max(person.household.sum(deductions))
