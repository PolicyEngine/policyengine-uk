from policyengine_uk.model_api import *


class benunit_is_liable_for_household_rent(Variable):
    value_type = bool
    entity = BenUnit
    label = "Liable for the household's rent"
    documentation = (
        "Whether this family is liable for rent (benunit_is_rent_liable) "
        "other than as boarders or lodgers paying the householder. "
        "benunit_rent includes what members pay the householder, so a family "
        "whose only liability is that payment reads as rent-liable there; "
        "here it does not, and each member's own liability is "
        "pays_rent_to_householder. The non-dependant rules read this flag: "
        "a member of a liable family is not a non-dependant, while in a "
        "boarder's or lodger's family only those liable to pay the "
        "householder leave the count."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
    )

    def formula(benunit, period, parameters):
        pays_householder = benunit.any(
            benunit.members("pays_rent_to_householder", period)
        )
        return benunit("benunit_is_rent_liable", period) & ~pays_householder
