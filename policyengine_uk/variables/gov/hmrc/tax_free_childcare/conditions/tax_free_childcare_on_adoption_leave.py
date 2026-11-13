from policyengine_uk.model_api import *


class tax_free_childcare_on_adoption_leave(Variable):
    value_type = bool
    entity = Person
    label = "on adoption leave for tax-free childcare"
    documentation = (
        "Reported adoption leave only. This legacy input alone no longer "
        "satisfies the Tax-Free Childcare work or minimum-income conditions. "
        "Use tax_free_childcare_qualifying_temporary_absence for regulation "
        "12 treatment only when its prior-work and applicable child/account "
        "conditions are satisfied; they are not inferred from this fact."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/12"
