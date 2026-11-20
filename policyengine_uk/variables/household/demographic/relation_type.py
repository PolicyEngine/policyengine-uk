from policyengine_uk.model_api import *


class RelationType(Enum):
    SINGLE = "Single"
    COUPLE = "Couple"


class relation_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = RelationType.SINGLE
    possible_values = RelationType
    label = "Whether single or a couple"
    documentation = (
        "Whether the claimant has a partner. A couple is two people who are "
        "married or civil partners in the same household, or who live "
        "together as if they were; the same definition applies across "
        "benefit and tax credit law. Dependent children and young persons "
        "are never the partner."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/137",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/39",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/17",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
    )

    def formula(benunit, period, parameters):
        claimants = add(benunit, period, ["is_claimant_or_partner"])
        return where(claimants >= 2, RelationType.COUPLE, RelationType.SINGLE)
