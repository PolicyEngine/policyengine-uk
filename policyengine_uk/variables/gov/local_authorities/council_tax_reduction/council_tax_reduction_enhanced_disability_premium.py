from policyengine_uk.model_api import *


class council_tax_reduction_enhanced_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age CTR enhanced disability premium"
    documentation = (
        "The model includes the enhanced disability premium in a working-age "
        "Council Tax Reduction applicable amount at the single rate, or at the "
        "couple rate where either or both members of a couple meet the "
        "scheme's condition "
        "(meets_council_tax_reduction_enhanced_disability_premium_condition). "
        "It pays a different premium from the legacy one "
        "(enhanced_disability_premium) in Scotland, Kingston upon Thames, "
        "Newham and, from 2023-24, Merton, where the councils count their own "
        "awards. The "
        "model pays the Housing Benefit amounts in every scheme. Both 2026-27 "
        "editions of Kingston upon Thames's scheme print £17.10 single and "
        "£24.50 couple (Sch 3 para 17(5)), and their introductions say the "
        "council uprates premiums as set out in the Prescribed Requirement "
        "Scheme. In December 2013 the council delegated each year's uprating, "
        "and the choice of its sources, to its Director of Finance. In July "
        "2014 it kept its scheme for 2015-17 apart from the uprating in Annex "
        "3, under which it takes working-age amounts from the Government's "
        "general uprating documents where the pension-age uprating lacks "
        "them; the 2026 pension-age uprating (S.I. 2026/27) has no adult "
        "enhanced premium. The model "
        "reads that mechanism as giving the Housing Benefit amounts; we found "
        "no decision that sets Kingston's own 2026-27 amounts. Pension-age "
        "Council Tax Reduction includes no adult enhanced disability premium."
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
