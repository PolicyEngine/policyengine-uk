from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


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
        # Reg 24B(1) orders children and qualifying young persons by date of
        # birth, taking the earliest first. Regs 24A and 24B were revoked from
        # 6 April 2026; the eldest child is then still the one for whom the
        # reg 43 saving is checked, as it holds if any child was born before
        # the cutoff.
        child_ranking = (
            person.get_rank(
                person.benunit,
                birth_day(person, period),
                condition=is_uc_child,
            )
            + 1
        )
        return where(is_uc_child, child_ranking, -1)
