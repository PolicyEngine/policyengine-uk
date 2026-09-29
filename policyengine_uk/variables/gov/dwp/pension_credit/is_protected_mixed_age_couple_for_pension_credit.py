from policyengine_uk.model_api import *


class is_protected_mixed_age_couple_for_pension_credit(Variable):
    label = "Protected mixed-age couple for Pension Credit"
    documentation = (
        "Whether this benefit unit is a mixed-age couple (one member has "
        "reached the qualifying age for State Pension Credit and the other has "
        "not) that SI 2019/37 art. 4 saves from the SPCA 2002 s.4(1A) "
        "exclusion: a member of the couple was entitled, as part of this same "
        "couple, to State Pension Credit or pension-age Housing Benefit on "
        "14 May 2019, and on every day since has been entitled to at least one "
        "of them as part of this couple (art. 4(2)). Art. 4(4) disregards days "
        "on Universal Credit after a migration notice where the couple claims "
        "again within three months. This is an input that defaults to false; "
        "survey datasets do not set it."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/uksi/2019/37/article/2",
    )
