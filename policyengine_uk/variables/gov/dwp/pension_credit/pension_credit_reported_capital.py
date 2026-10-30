from policyengine_uk.model_api import *


class pension_credit_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Pension Credit capital"
    documentation = (
        "Explicit complete countable-capital override for the claimant and "
        "partner together. A nonnegative value, including zero, replaces "
        "household and person-level capital sources. It must already reflect "
        "the regulation 19 valuation and Schedule V disregards. The default "
        "-1 means no complete override. In that case a nonnegative "
        "benunit_reported_capital replaces only financial proxies, while "
        "separately valued land and property remain counted; with neither "
        "report the household proxy and person-level sources apply. This "
        "variable does not derive from the financial-only observation. An "
        "override set directly applies only in the supplied assessment year."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/19",
    )

    def formula(benunit, period, parameters):
        return -1
