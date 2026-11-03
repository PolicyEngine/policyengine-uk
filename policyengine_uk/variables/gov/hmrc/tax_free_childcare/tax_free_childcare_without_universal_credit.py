from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.tax_free_childcare._top_up import (
    tax_free_childcare_top_up,
)


class tax_free_childcare_without_universal_credit(Variable):
    value_type = float
    entity = Person
    label = "Tax-Free Childcare top-up without a Universal Credit claim"
    documentation = (
        "The top-up this child would get from Tax-Free Childcare if the "
        "family did not claim Universal Credit, for the whole year. It is "
        "tax_free_childcare's amount on "
        "tax_free_childcare_eligible_without_universal_credit, and it is "
        "what forgoes_universal_credit_for_tax_free_childcare weighs "
        "against the award."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "tax_free_childcare_eligible_without_universal_credit"

    def formula(person, period, parameters):
        periods = parameters(
            period
        ).gov.hmrc.tax_free_childcare.declaration_periods_per_year
        eligible = person.benunit(
            "tax_free_childcare_eligible_without_universal_credit", period
        )
        return tax_free_childcare_top_up(person, period, parameters, eligible * periods)
