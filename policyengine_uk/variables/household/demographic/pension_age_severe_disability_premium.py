from policyengine_uk.model_api import *


class pension_age_severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium for pension-age Housing Benefit and CTR"
    documentation = (
        "The severe disability premium in the Housing Benefit and Council Tax "
        "Reduction applicable amount of a family over State Pension age. "
        "The Pension Credit severe disability addition supplies the qualifying "
        "benefit, couple, carer and rate calculation. Both partners must "
        "qualify unless the non-qualifying partner is blind. For that route "
        "the model assumes the qualifying partner claims Housing Benefit, "
        "as a couple may arrange under regulation 63(1). Housing Benefit's "
        "own non-dependant test is applied separately: a qualifying young "
        "person aged 18 or over in another family can block this premium "
        "although Pension Credit ignores them. Its modelled residence "
        "exceptions match the working-age Housing Benefit premium, so both "
        "use has_non_dependant_for_severe_disability_premium. Carers are "
        "attributed by is_cared_for_by_carer_benefit_recipient, including "
        "carers in other benefit units in the household. The premium inherits "
        "the documented limitations of those shared helpers, including the "
        "omission of Universal Credit carer-element awards."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/63",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/2/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        pension_age = benunit.any(benunit.members("is_SP_age", period))
        addition = benunit("severe_disability_minimum_guarantee_addition", period)
        # HB(SPC) Sch 3 para 6(6) and reg 3 have the same residence
        # exceptions as working-age HB Sch 3 para 14(4) and reg 3.
        no_non_dependant = ~benunit(
            "has_non_dependant_for_severe_disability_premium", period
        )
        return where(pension_age & no_non_dependant, addition, 0)
