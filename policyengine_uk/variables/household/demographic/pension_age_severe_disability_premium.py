from policyengine_uk.model_api import *


class pension_age_severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium for pension-age Housing Benefit and CTR"
    documentation = (
        "The severe disability premium in the Housing Benefit and Council Tax "
        "Reduction applicable amount of a family over State Pension age. In "
        "law its qualifying benefits (Attendance Allowance, the care component "
        "of DLA at the middle or highest rate, the daily living component of "
        "PIP at either rate, Armed Forces Independence Payment and their "
        "Scottish equivalents), its conditions and its amounts (one rate, or "
        "two for a couple who both qualify and have no paid carer) are the "
        "same as those of the Pension Credit severe disability additional "
        "amount. So this premium reads that variable, and Housing Benefit, "
        "Council Tax Reduction and Pension Credit share one definition: the "
        "premium cannot drop out of the Housing Benefit applicable amount "
        "when Guarantee Credit ends. It therefore also shares that variable's "
        "modelling simplifications."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3035/schedule/2/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        pension_age = benunit.any(benunit.members("is_SP_age", period))
        addition = benunit("severe_disability_minimum_guarantee_addition", period)
        return where(pension_age, addition, 0)
