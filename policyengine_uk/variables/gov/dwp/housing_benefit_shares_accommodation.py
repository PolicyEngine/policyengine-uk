from policyengine_uk.model_api import *


class housing_benefit_shares_accommodation(Variable):
    value_type = bool
    entity = BenUnit
    label = "Lacks exclusive use of self-contained accommodation (Housing Benefit)"
    documentation = (
        "Whether the family lacks exclusive use of two or more rooms, or of "
        "one room with a bathroom, toilet and kitchen. Rooms shared only with "
        "the family's own household, its non-dependants or people who pay it "
        "rent still count as exclusive. A boarder or lodger shares the "
        "householder's rooms, and in a household whose rent is shared every "
        "liable family shares the others' rooms. The household input "
        "is_shared_accommodation marks any other case."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D"

    def formula(benunit, period, parameters):
        # HB Regs 2006 reg 13D(2)(b): exclusive use of two or more rooms, or
        # of one room, a bathroom and toilet and a kitchen or facilities for
        # cooking, excluding rooms shared with anyone other than a member of
        # the household, a non-dependant or a person who pays rent.
        person = benunit.members
        household_input = benunit.any(
            person.household("is_shared_accommodation", period)
        )
        boarder_or_lodger = benunit.any(person("pays_rent_to_householder", period))
        rent_is_shared = benunit.any(
            person.household.any(
                person.benunit("liable_for_share_of_household_rent", period)
            )
        )
        liable = benunit("benunit_is_rent_liable", period)
        return household_input | boarder_or_lodger | (rent_is_shared & liable)
