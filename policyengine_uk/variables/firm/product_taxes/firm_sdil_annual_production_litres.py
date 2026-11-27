from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_sdil_annual_production_litres(Variable):
    label = "Soft drinks levy small producer test litres"
    documentation = (
        "Litres of chargeable soft drinks produced in the year by the firm "
        "as producer and by persons connected with it, for the small "
        "producer test (Finance Act 2017 ss.37-38). Defaults to the firm's "
        "own higher and lower rate litres. Supply it where the firm is in "
        "a group, or where it imports drinks whose producer's output "
        "differs from its own. A value of 0 or below is read as not "
        "supplied, so the firm's own litres are used."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    reference = [
        "https://www.legislation.gov.uk/ukpga/2017/10/section/37",
        "https://www.legislation.gov.uk/ukpga/2017/10/section/38",
    ]
    adds = ["firm_sdil_litres_higher_rate", "firm_sdil_litres_lower_rate"]
