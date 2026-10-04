from policyengine_uk.model_api import *
from policyengine_core.enums import EnumArray
from policyengine_uk.variables.household.demographic.tenure_type import (
    TenureType,
)


class benunit_tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = BenUnit
    label = "Tenure type of the family"
    documentation = (
        "The family's own tenure. A boarder or lodger rents privately from "
        "the householder whatever the household's tenure, so a lodger in a "
        "council or housing association home is a private renter. Other "
        "families take the household's tenure."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/20",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13C",
    )

    def formula(benunit, period, parameters):
        household_tenure = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )
        # UC private rented sector rules apply to renters liable to anyone
        # other than a provider of social housing (UC Regs 2013 Sch 4 para
        # 20); a householder is not a social landlord (HB Regs 2006 reg
        # 13C(5)(a)).
        pays_householder = benunit.any(
            benunit.members("pays_rent_to_householder", period)
        )
        return EnumArray(
            where(
                pays_householder,
                TenureType.RENT_PRIVATELY.index,
                household_tenure,
            ).astype(np.int16),
            TenureType,
        )
