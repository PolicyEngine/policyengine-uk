from policyengine_uk.model_api import *


class tax_free_childcare_qualifying_child(Variable):
    value_type = bool
    entity = Person
    label = "qualifying child for tax-free childcare"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/4",
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/5",
    ]

    def formula(person, period, parameters):
        meets_age_condition = person(
            "tax_free_childcare_child_age_eligible",
            period,
        )
        is_parent = person("is_parent", period)
        looked_after_by_local_authority = person(
            "is_looked_after_by_local_authority",
            period,
        )
        return meets_age_condition & ~is_parent & ~looked_after_by_local_authority
