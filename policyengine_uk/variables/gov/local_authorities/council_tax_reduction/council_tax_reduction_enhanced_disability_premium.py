from policyengine_uk.model_api import *


class council_tax_reduction_enhanced_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age CTR enhanced disability premium"
    documentation = (
        "The enhanced disability premium in a working-age Council Tax "
        "Reduction applicable amount: the single rate, or the couple rate "
        "where either or both members of a couple meet the scheme's condition "
        "(meets_council_tax_reduction_enhanced_disability_premium_condition). "
        "It differs from the legacy premium (enhanced_disability_premium) in "
        "Scotland, Merton, Kingston upon Thames and Newham, whose schemes name "
        "their own awards. The model pays the Housing Benefit amounts in every "
        "scheme, though Kingston upon Thames's 2026-27 scheme sets lower ones "
        "(£17.10 single, £24.50 couple). Pension-age Council Tax Reduction has "
        "no adult enhanced disability premium."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/4",
    )

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        person = benunit.members
        qualifies = benunit.any(
            person("is_claimant_or_partner", period)
            & person(
                "meets_council_tax_reduction_enhanced_disability_premium_condition",
                period,
            )
        )
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        weekly_amount = single * dis.enhanced_single + couple * dis.enhanced_couple
        return weekly_amount * WEEKS_IN_YEAR * qualifies
