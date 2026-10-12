from policyengine_uk.model_api import *


class is_responsible_for_child_or_qualifying_young_person_for_child_tax_credit(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = "Responsible for a child or qualifying young person for tax credits"
    documentation = (
        "Whether the claimant (or either joint claimant) is responsible for "
        "at least one child or qualifying young person under the Child Tax "
        "Credit rules, which Working Tax Credit also applies. Benefit-unit "
        "membership stands in for 'normally living with'."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/8",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/3",
        "https://www.legislation.gov.uk/uksi/2002/2005/regulation/2",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        return benunit.any(
            person("is_child_or_qualifying_young_person_for_child_tax_credit", period)
            & ~person("is_claimant_or_partner", period)
        )
