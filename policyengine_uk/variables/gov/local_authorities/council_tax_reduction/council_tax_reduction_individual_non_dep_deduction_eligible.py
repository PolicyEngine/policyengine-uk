from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for CTR non-dependent deduction"
    documentation = (
        "An adult outside the claimant's family who is not liable for rent. "
        "Someone jointly and severally liable for the council tax with the "
        "claimant (a joint tenant or other sharer of the rent) and someone "
        "liable to the claimant on a commercial basis (a boarder or lodger) "
        "is not a non-dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/wsi/2013/3029",
        "https://www.legislation.gov.uk/ssi/2021/249",
    )

    def formula(person, period, parameters):
        # SI 2012/2885 reg 9(2)(d)-(e) and the Welsh and Scottish equivalents.
        return (
            (person("age", period) >= 18)
            & ~person.benunit("benunit_contains_household_head", period)
            & ~person.benunit("benunit_is_rent_liable", period)
        )
