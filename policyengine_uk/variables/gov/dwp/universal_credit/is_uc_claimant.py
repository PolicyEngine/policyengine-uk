from policyengine_uk.model_api import *


class is_uc_claimant(Variable):
    """Claimant or partner, rather than a dependent member of the benefit unit.

    Datasets should supply this from recorded relationships. The calculator
    fallback includes the family head, identified parents, and adults who are
    not UC qualifying children. A young partner in education, or a dependent
    adult outside the UC child definition, needs an explicit input when those
    relationships cannot be inferred. This flag does not establish eligibility.
    """

    value_type = bool
    entity = Person
    label = "Universal Credit claimant or partner"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/39",
        "https://www.gov.uk/universal-credit/eligibility",
    )

    def formula(person, period, parameters):
        return (
            person("is_benunit_head", period)
            | person("is_parent", period)
            | (
                person("is_adult", period)
                & ~person(
                    "is_child_or_qualifying_young_person_for_universal_credit", period
                )
            )
        )
