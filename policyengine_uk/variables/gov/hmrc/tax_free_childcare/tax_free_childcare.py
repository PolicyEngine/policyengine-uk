from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.tax_free_childcare._top_up import (
    tax_free_childcare_top_up,
)


class tax_free_childcare(Variable):
    value_type = float
    entity = Person
    label = "government contribution through tax-free childcare"
    definition_period = YEAR
    unit = GBP
    defined_for = "tax_free_childcare_eligible"
    # Note: tax_free_childcare_eligible is a BenUnit variable implicitly cast to Person level

    def formula(person, period, parameters):
        return tax_free_childcare_top_up(
            person,
            period,
            parameters,
            person.benunit("tax_free_childcare_eligible_declaration_periods", period),
        )
