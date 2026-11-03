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
        # Non-dependants are not liable for rent (para 9(2)(d)), and each
        # counts in one Universal Credit claim only (para 9(2)(f)): see
        # uc_non_dependants_counted.
        person = benunit.members
        deductions = person("uc_individual_non_dep_deduction", period) * person(
            "is_non_dependant_of_household_head", period
        )
        counted = benunit("uc_non_dependants_counted", period)
        return counted * benunit.max(person.household.sum(deductions))
