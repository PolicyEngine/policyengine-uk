from policyengine_uk.model_api import *


class is_responsible_for_child_or_young_person_for_council_tax_reduction(Variable):
    value_type = bool
    entity = BenUnit
    label = "Responsible for a child or young person for Council Tax Reduction"
    documentation = (
        "Whether the applicant or partner is responsible for a child or young "
        "person in the same household, under the young person definition of "
        "the Council Tax Reduction scheme that applies to the family "
        "(is_child_or_young_person_for_council_tax_reduction). Benefit-unit "
        "membership stands in for 'normally lives with'."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/7",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/10",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/7",
    )

    def formula(benunit, period, parameters):
        return benunit.any(
            benunit.members(
                "is_child_or_young_person_for_council_tax_reduction", period
            )
        )
