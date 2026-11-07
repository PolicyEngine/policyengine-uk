from policyengine_uk.model_api import *


class council_tax_reduction_working_age_passported(Variable):
    value_type = bool
    entity = BenUnit
    label = "Passported to the maximum working-age council tax reduction"
    documentation = (
        "Whether the applicant or partner is on Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance and has no award of Universal Credit "
        "(council_tax_reduction_universal_credit_award). In Scotland such an "
        "applicant gets the maximum reduction (SSI 2021/249 reg 13(11)); in "
        "Wales the scheme disregards the whole of their income and capital "
        "(WSI 2013/3029 "
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
        universal_credit_award = benunit(
            "council_tax_reduction_universal_credit_award", period
        )
        return income_related_benefit & ~universal_credit_award
