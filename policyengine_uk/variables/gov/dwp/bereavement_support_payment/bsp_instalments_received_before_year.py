from policyengine_uk.model_api import *


class bsp_instalments_received_before_year(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = -1
    quantity_type = STOCK
    label = "BSP instalments received before year"
    documentation = "Known count of all standard/higher instalments already received for this same award before requested year; -1unknown. Needs a genuine current-year history fact, not stale prior-year carry. This fact must be genuinely supplied for the exact requested year; derived values and carried prior-year facts do not establish current receipt history."
    reference = (
        "https://www.gov.uk/bereavement-support-payment/what-youll-get",
        "https://www.nidirect.gov.uk/articles/bereavement-support-payment",
        "https://www.legislation.gov.uk/uksi/2017/410/regulation/3",
    )
