from policyengine_uk.model_api import *


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Carer premium"
    definition_period = YEAR
    reference = (
        "The Social Security Amendment (Carer Premium) Regulations 2002"
    )
    unit = GBP

    def formula(benunit, period, parameters):
        carers = benunit("num_carers", period.this_year)
        CP = parameters(period).gov.dwp.carer_premium
        weekly_premium = select(
            [carers == 0, carers == 1, carers == 2],
            [0, CP.single, CP.couple],
        )
        return weekly_premium * WEEKS_IN_YEAR
