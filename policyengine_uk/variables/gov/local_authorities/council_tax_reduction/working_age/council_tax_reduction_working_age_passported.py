from policyengine_uk.model_api import *


class council_tax_reduction_working_age_passported(Variable):
    value_type = bool
    entity = BenUnit
    label = "Passported to the maximum working-age council tax reduction"
    documentation = (
        "Whether the claimant or partner is on Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance and not on Universal Credit. In Scotland such a claimant "
        "gets the maximum reduction (SSI 2021/249 reg 13(11)); in Wales the "
        "whole of their income and capital is disregarded (WSI 2013/3029 "
        "Sch 9 para 8, Sch 10 para 8)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/13",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/10/paragraph/8",
    )

    def formula(benunit, period, parameters):
        income_related_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        return income_related_benefit & ~has_universal_credit
