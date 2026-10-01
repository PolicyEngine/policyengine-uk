from policyengine_uk.model_api import *


class is_responsible_for_child_under_5_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Responsible for a child under 5 for Universal Credit"
    documentation = (
        "Whether this person is responsible for a child under 5 (the age is "
        "the young child age limit of the housing cost contribution "
        "exemption, Sch 4 para 16(2)(i)). Responsibility follows UC reg 4, "
        "with benefit-unit membership for 'normally lives with': the claimant "
        "and any partner are each responsible for their unit's children, so "
        "both members of a couple are, and a member who is neither, such as "
        "an adult son, is responsible for none (reg 4(4)). A child looked "
        "after by a local authority is no one's responsibility (reg 4(6)(a))."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/40",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
        claimant = person("is_uc_claimant", period)
        # Anyone under the limit is a child (under 16, WRA 2012 s.40).
        young_child = (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            & ~claimant
            & (person("age", period) < p.young_child_age_limit)
        )
        return claimant & person.benunit.any(young_child)
