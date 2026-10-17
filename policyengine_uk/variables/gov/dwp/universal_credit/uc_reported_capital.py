from policyengine_uk.model_api import *


class uc_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Universal Credit capital"
    documentation = (
        "Explicit complete countable-capital override for the claimant and "
        "partner together. A nonnegative value, including zero, replaces "
        "ordinary financial, property and person-level capital sources before "
        "the existing regulation 77 company holding substitution; it must "
        "already reflect programme valuations and Schedule 10 disregards. "
        "An override of zero plus company capital of GBP 8,000 therefore "
        "assesses GBP 8,000. The default "
        "-1 means no complete override: benunit_reported_capital then replaces "
        "only financial proxies, with countable property assessed separately. "
        "Property allocation depends only on claimant/partner adult counts "
        "and is independent of other units' financial reports. The residual "
        "financial pool is shared among units with neither report; under this "
        "inherited convention, another unit's financial report or complete "
        "override can change a missing-report unit's capital. The complete "
        "override consumes its amount from the financial pool, taking "
        "precedence over the same unit's financial report. "
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
