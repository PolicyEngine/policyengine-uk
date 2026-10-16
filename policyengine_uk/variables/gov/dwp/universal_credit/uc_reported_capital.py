from policyengine_uk.model_api import *


class uc_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Universal Credit capital"
    documentation = (
        "Explicit complete countable-capital override for the claimant and "
        "partner together. A nonnegative value, including zero, replaces "
        "financial, property and person-level capital sources; it must already "
        "reflect programme valuations and Schedule 10 disregards. The existing "
        "regulation 77 company holding substitution still applies. The default "
        "-1 means no complete override: benunit_reported_capital then replaces "
        "only financial proxies, with countable property assessed separately. "
        "This variable does not derive from the financial-only FRS total. "
        "An override set directly applies only in the supplied assessment year."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/18",
    )

    def formula(benunit, period, parameters):
        return -1
