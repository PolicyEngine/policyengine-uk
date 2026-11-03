from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_kingston_upon_thames_area,
    is_merton_area,
    is_newham_area,
    is_scotland_scheme,
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
        "2022. Merton and Kingston upon Thames count the PIP daily living "
        "component at either rate and omit armed forces independence payment; "
        "Newham counts the PIP daily living component at either rate and "
        "armed forces independence payment. Those three councils count an "
        "award only for a person under the qualifying age for State Pension "
        "Credit. The model applies each council's own list from the first "
        "scheme year whose text supports it (qualifying_benefits_in_effect): "
        "Merton's from 2023-24, and Kingston upon Thames's and Newham's in "
        "every model year, since their texts support them from 2013-14. "
        "Before Merton's first year, and in every other scheme, it applies "
        "the Housing Benefit condition "
        "(receives_enhanced_disability_premium_qualifying_benefit, under the "
        "same age limit). Welsh councils apply that condition under W.S.I. "
        "2013/3029 Sch 7 para 12. Westminster City Council publishes a "
        "2026-27 summary of its working-age scheme without the premium's "
        "qualifying awards. Its Council's annual resolutions describe the "
        "scheme as based on the Default Scheme Regulations, with war pensions "
        "and Armed Forces Compensation Scheme payments disregarded in full "
        "and, from 2020, updated for the amendments to the Prescribed "
        "Requirements Regulations, and its budget reports since 2022 say it "
        "mirrors the original Default Scheme Regulations; the council has also "
        "changed provisions those descriptions leave out. No scheme text "
        "states the qualifying awards, so the model assumes the Housing "
        "Benefit condition there. "
        "Oxford City Council sets "
        "its working-age award from income bands, so the premium does not "
        "reach it."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/1/paragraph/12/2021-04-01",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
        "https://www.merton.gov.uk/system/files/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202023-24_0.pdf",
        "https://www.merton.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202026-27.pdf",
        "https://moderngov.kingston.gov.uk/mgAi.aspx?ID=20744",
        "https://www.legislation.gov.uk/uksi/2012/2886/appendix/3/regulation/12/made",
        "https://www.kingston.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%202026%20-%202027.pdf",
        "https://mgov.newham.gov.uk/documents/s74450/Appendix%201%20-%20LB%20Newham%20Local%20CTR%20Scheme_16_01_13.pdf",
        "https://www.newham.gov.uk/downloads/file/10753/council-tax-reduction-scheme-2026",
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
            own_list = receives(p.qualifying_benefits) & under_age
            # Before the first scheme year whose text supports the council's
            # own list, the model applies the Housing Benefit condition.
            return where(p.qualifying_benefits_in_effect, own_list, housing_benefit)

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
            ],
            [
                scottish,
                council_condition(la.merton),
                council_condition(la.kingston_upon_thames),
                council_condition(la.newham),
            ],
            default=housing_benefit,
        )
