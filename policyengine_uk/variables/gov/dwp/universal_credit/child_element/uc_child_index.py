from policyengine_uk.model_api import *


class uc_child_index(Variable):
    value_type = int
    entity = Person
    label = "Universal Credit child reference number"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24B",
        "https://www.gov.uk/universal-credit/what-youll-get",
    )

    def formula(person, period, parameters):
        is_uc_child = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        ) & ~person("is_uc_claimant", period)
        # Reg 24B orders children and qualifying young persons by date of
        # birth, eldest first, where the claimant is their parent.
        child_ranking = (
            person.get_rank(
                person.benunit,
                person("date_of_birth", period),
                condition=is_uc_child,
            )
            + 1
        )
        return where(is_uc_child, child_ranking, -1)
