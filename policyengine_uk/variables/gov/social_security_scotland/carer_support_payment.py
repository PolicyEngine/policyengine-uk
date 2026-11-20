from policyengine_uk.model_api import *


class carer_support_payment(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment"
    documentation = (
        "The Carer Support Payment component of Carer Support, which replaces "
        "Carer's Allowance for eligible carers living in Scotland, after the "
        "overlapping-benefit reduction: it is reduced by any overlapping "
        "benefit, such as State Pension, and is £0 where that benefit is at "
        "least as much. The Scottish Carer Supplement paid with it from 15 "
        "March 2026 is a separate component: see scottish_carer_supplement. "
        "The comparison is made on annual amounts, which equals the weekly "
        "rule when the overlapping benefit is paid at a constant rate all year. "
        "Where the overlapping benefit is above the carer rate in some weeks "
        "and lower or absent in others, for example when it is paid for part "
        "of the year, the annual comparison pays less than the weekly rule "
        "would; annual inputs carry no dates to do better."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.mygov.scot/carer-support-payment",
        "https://www.legislation.gov.uk/asp/2018/9/part/4",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/3",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
    )

    def formula(person, period, parameters):
        pre_overlap = person("carer_support_payment_pre_overlap", period)
        overlapping = person("carer_support_payment_overlapping_benefits", period)
        return max_(pre_overlap - overlapping, 0)
