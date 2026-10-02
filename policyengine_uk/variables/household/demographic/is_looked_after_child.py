from policyengine_uk.model_api import *


class is_looked_after_child(Variable):
    value_type = bool
    entity = Person
    label = "Child looked after by a local authority"
    documentation = (
        "Whether this person is flagged is_looked_after_by_local_authority "
        "and is under 18. Only a child, a person under 18, can be looked "
        "after by a local authority (Children Act 1989 ss.22(1) and 105(1); "
        "the Scottish and Welsh definitions are also limited to children), "
        "so the flag has no effect at 18 or over: Universal Credit treats "
        "the carer as responsible for a qualifying young person aged 18 or "
        "19, and Housing Benefit counts them as a household member."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1989/41/section/22",
        "https://www.legislation.gov.uk/ukpga/1989/41/section/105",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
    )

    def formula(person, period, parameters):
        age_limit = parameters(
            period
        ).household.demographic.looked_after_child_age_limit
        return person("is_looked_after_by_local_authority", period) & (
            person("age", period) < age_limit
        )
