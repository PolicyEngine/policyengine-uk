from policyengine_uk.model_api import *


class BSPInitialPaymentRate(Enum):
    UNKNOWN = "Unknown initial payment rate"
    STANDARD = "Qualified standard-rate initial payment"
    HIGHER = "Qualified higher-rate initial payment"


class bsp_initial_payment_rate(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = BSPInitialPaymentRate
    default_value = BSPInitialPaymentRate.UNKNOWN
    label = "BSP initial payment rate"
    documentation = "Independently qualified initial award category: UNKNOWN,STANDARD,HIGHER. Later initial-payment adjustments/top-ups excluded; normal explicit final-cash override remains available. These fixed actual receipt facts require genuine supplied provenance; current-year defaults, calculated caches and imputed dates are not evidence."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )
