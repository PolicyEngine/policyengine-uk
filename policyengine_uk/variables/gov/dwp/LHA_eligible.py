from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


class LHA_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligibility for Local Housing Allowance"
    documentation = (
        "Whether the benefit unit's Housing Benefit eligible rent is set by the "
        "Local Housing Allowance: it rents, no member is in social housing, and "
        "its home is not a houseboat, caravan or mobile home."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13C",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13C",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/14C",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/14C",
    )

    def formula(benunit, period, parameters):
        renting = benunit("benunit_is_renting", period)
        anyone_in_social_housing = benunit.any(
            benunit.members("in_social_housing", period)
        )
        # No maximum rent (LHA) is determined where the claim relates to rent
        # for "a houseboat, caravan or mobile home which he occupies as his
        # home" (SI 2006/213 and SI 2006/214 reg 13C(5)(d)(i); Northern
        # Ireland: SR 2006/405 and SR 2006/406 reg 14C(5)(d)(i)). A rent
        # officer (in Northern Ireland, the Housing Executive) sets a maximum
        # rent under the older rules instead (regs 12C, 13 and 14). The model
        # has no such determination, so Housing Benefit uses the rent.
        accommodation = benunit.value_from_first_person(
            benunit.members.household("accommodation_type", period)
        )
        mobile_home = accommodation == accommodation.possible_values.MOBILE
        return renting & ~anyone_in_social_housing & ~mobile_home
