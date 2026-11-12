from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_kingston_upon_thames_area,
    is_merton_area,
    is_newham_area,
    is_scotland_scheme,
    is_westminster_area,
)


class meets_council_tax_reduction_enhanced_disability_premium_condition(Variable):
    value_type = bool
    entity = Person
    label = "Meets the working-age CTR enhanced disability premium condition"
    documentation = (
        "The model checks whether this person, as an applicant or partner, "
        "meets the enhanced disability premium condition of the working-age "
        "Council Tax Reduction scheme that covers their household. Scottish "
        "councils count attendance allowance at either rate from 1 April "
        "2023, and the Scottish Ministers removed the age limit from 20 June "
        "2022. Merton counts the PIP daily living component at either rate "
        "and omits armed forces independence payment; Newham counts the PIP "
        "daily living component at either rate and armed forces independence "
        "payment. In Westminster the model applies "
        "the Default Scheme's list (S.I. 2012/2886 Sch 3 para 12), which "
        "counts the PIP daily living component at either rate and omits armed "
        "forces independence payment: the council has approved the same "
        "scheme, based on the Default Scheme Regulations, since 2013/14, and "
        "its Cabinet says from December 2020 that its local scheme mirrors "
        "those Regulations, though the model cites no full Westminster scheme "
        "text. Those three councils count an award only for a person under the "
        "qualifying age for State Pension Credit, and their lists start on or "
        "before 1 April 2013 and apply in every model year. In Kingston upon "
        "Thames the model reads is_enhanced_disabled_for_benefits, with no age "
        "limit; that variable's documentation says what sets it. The council's "
        "texts from 2023-24 print a wider list with an age limit (Sch 3 para "
        "12), and issue #2881 lists what the model needs to apply it. In "
        "every other scheme the model applies the Housing Benefit condition "
        "(receives_enhanced_disability_premium_qualifying_benefit, under the "
        "same age limit). Welsh councils apply that condition under W.S.I. "
        "2013/3029 Sch 7 para 12. Oxford City Council sets its working-age "
        "award from income bands, so the premium does not reach it."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/1/paragraph/12/2021-04-01",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
        "https://web.archive.org/web/20150530202253id_/http://www.merton.gov.uk/council_tax_reduction_scheme_l_b_merton_april_2013_with_uprated_amounts_final_310113-2.pdf",
        "https://www.merton.gov.uk/system/files/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202023-24_0.pdf",
        "https://www.merton.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202026-27.pdf",
        "https://www.legislation.gov.uk/uksi/2012/2886/appendix/3/regulation/12/made",
        "https://www.kingston.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%202026%20-%202027.pdf",
        "https://mgov.newham.gov.uk/documents/s74450/Appendix%201%20-%20LB%20Newham%20Local%20CTR%20Scheme_16_01_13.pdf",
        "https://www.newham.gov.uk/downloads/file/10753/council-tax-reduction-scheme-2026",
        "https://web.archive.org/web/20240621074656id_/https://committees.westminster.gov.uk/documents/s40219/Report%20of%20the%20Cabinet%2014%20December%202020%20-Council%20Tax%20Discounts.pdf",
        "https://committees.westminster.gov.uk/mgAi.aspx?ID=22982",
        "https://www.westminster.gov.uk/sites/default/files/media/documents/business-and-financial-planning-2026-27-to-2028-29.pdf",
        "https://committees.westminster.gov.uk/ieDecisionDetails.aspx?ID=1181",
    )

    def formula(person, period, parameters):
        la = parameters(period).gov.local_authorities
        household = person.household
        country = household("country", period)
        local_authority = household("local_authority", period)
        under_age = ~person("has_attained_state_pension_credit_qualifying_age", period)

        def receives(benefits):
            return add(person, period, benefits) > 0

        housing_benefit = (
            person("receives_enhanced_disability_premium_qualifying_benefit", period)
            & under_age
        )

        def council_condition(council):
            p = council.council_tax_reduction.enhanced_disability_premium
            return receives(p.qualifying_benefits) & under_age

        p = la.scotland.council_tax_reduction.working_age.enhanced_disability_premium
        scottish = receives(p.qualifying_benefits) & (
            under_age | (not p.age_limit_applies)
        )
        return select(
            [
                is_scotland_scheme(country),
                is_merton_area(local_authority, country),
                is_kingston_upon_thames_area(local_authority, country),
                is_newham_area(local_authority, country),
                is_westminster_area(local_authority, country),
            ],
            [
                scottish,
                council_condition(la.merton),
                person("is_enhanced_disabled_for_benefits", period),
                council_condition(la.newham),
                council_condition(la.westminster),
            ],
            default=housing_benefit,
        )
