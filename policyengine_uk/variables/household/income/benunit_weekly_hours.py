from policyengine_uk.model_api import *


class benunit_weekly_hours(Variable):
    value_type = float
    entity = BenUnit
    label = "Average weekly hours worked by adults in the benefit unit"
    definition_period = YEAR
    unit = "hour"

    adds = ["weekly_hours"]
