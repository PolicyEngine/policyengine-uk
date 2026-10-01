from policyengine_uk.model_api import *


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance"
    documentation = (
        "Carer's Allowance payable after the overlapping-benefit adjustment: "
        "the allowance is reduced by any other personal benefit that overlaps "
        "with it, such as State Pension, and only the balance is paid. The "
        "comparison is made on annual amounts, which equals the weekly rule "
        "when the overlapping benefit is paid at a constant rate all year."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/4",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/12",
    )

    def formula(person, period, parameters):
        pre_overlap = person("carers_allowance_pre_overlap", period)
        overlapping = person("carers_allowance_overlapping_benefits", period)
        return max_(pre_overlap - overlapping, 0)
