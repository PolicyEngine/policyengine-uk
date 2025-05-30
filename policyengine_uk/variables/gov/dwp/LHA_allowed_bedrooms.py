from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10/2021-04-06"

    def formula(benunit, period, parameters):
        """
        LHA allows for one room for:
        a) The benefit unit adult(s)
        b) Each person over 16 outside the benefit unit
            but within the household
        Children must share rooms in pairs unless they are
        opposite-sex and one is over 10. The number of bedrooms
        allowed under LHA rules is the minimum number of bedrooms
        required to allocate people satisfying these rules.
        """
        person = benunit.members
        age = person("age", period)
        male = person("is_male", period)
        under_16 = age < 16
        under_10 = age < 10
        child_over_10 = ~under_10 & under_16
        # One room each for over-16s outside the benefit unit
        non_dependants = benunit.max(
            person.household.sum(~under_16)
        ) - benunit.sum(~under_16)
        boys_under_10 = benunit.sum(under_10 & male)
        boys_over_10 = benunit.sum(child_over_10 & male)
        girls_under_10 = benunit.sum(under_10 & ~male)
        girls_over_10 = benunit.sum(child_over_10 & ~male)
        # First, have over-10s share where possible
        over_10_rooms = (boys_over_10 + 1) // 2 + (girls_over_10 + 1) // 2
        # There may children over 10 still not sharing
        space_for_boy_under_10 = boys_over_10 % 2
        space_for_girl_under_10 = girls_over_10 % 2
        # Have those spaces filled where possible by children under 10
        left_over_boys_under_10 = max_(
            boys_under_10 - space_for_boy_under_10, 0
        )
        left_over_girls_under_10 = max_(
            girls_under_10 - space_for_girl_under_10, 0
        )
        # The remaining children must share in pairs
        under_10_rooms = (
            left_over_boys_under_10 + left_over_girls_under_10 + 1
        ) // 2
        return 1 + non_dependants + over_10_rooms + under_10_rooms
