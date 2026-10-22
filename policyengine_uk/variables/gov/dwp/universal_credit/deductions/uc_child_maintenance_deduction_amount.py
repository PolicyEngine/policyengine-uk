from policyengine_uk.model_api import *


class uc_child_maintenance_deduction_amount(Variable):
    label = "UC child maintenance cash deduction demand"
    documentation = (
        "Annual cash demand for ongoing child maintenance, fees and arrears, before "
        "the statutory ceiling and penny floor. Supply the actual amount separately "
        "from other third party debt; no maintenance incidence is imputed. The "
        "arrears-only flat rate is £36.40 a month from 4 July 2019; ongoing "
        "maintenance and fees depend on the amount due."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/380/schedule/7"
