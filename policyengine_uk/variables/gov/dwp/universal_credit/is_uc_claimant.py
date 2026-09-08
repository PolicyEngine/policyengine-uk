from policyengine_uk.model_api import *


class is_uc_claimant(Variable):
    """Claimant or partner, rather than a dependent member of the benefit unit.

    Datasets should supply this from recorded relationships. The calculator
    fallback includes the family head, identified parents, and adults, except
    UC qualifying young people in a benefit unit with an identified parent.
    Education defaults to tertiary education at ages 18 and 19, so treating
    those ages as dependants requires qualifying education and any applicable
    entry and terminal-date inputs. A partner in qualifying education who is
    not identified as a head or parent, or a dependent adult outside the UC
    child definition, needs an explicit input when relationships remain
    ambiguous. This flag does not establish eligibility.
    """

    value_type = bool
    entity = Person
    label = "Universal Credit claimant or partner"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/39",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3/2",
        "https://www.gov.uk/universal-credit/eligibility",
    )

    def formula(person, period, parameters):
        has_parent = add(person.benunit, period, ["is_parent"]) > 0
        qualifying_child = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        return (
            person("is_benunit_head", period)
            | person("is_parent", period)
            | (person("is_adult", period) & ~(qualifying_child & has_parent))
        )
