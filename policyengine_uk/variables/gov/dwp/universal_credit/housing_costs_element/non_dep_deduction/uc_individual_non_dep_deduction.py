from policyengine_uk.model_api import *


class uc_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit non-dependent deduction (individual)"
    definition_period = YEAR
    unit = GBP
    defined_for = "uc_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
        return p.amount * MONTHS_IN_YEAR
