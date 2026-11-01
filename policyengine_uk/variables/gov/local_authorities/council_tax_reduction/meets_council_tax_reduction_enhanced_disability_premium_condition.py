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
        "Credit. The model applies the Housing Benefit condition elsewhere "
        "(receives_enhanced_disability_premium_qualifying_benefit, under the "
        "same age limit). Welsh councils apply that condition under W.S.I. "
        "2013/3029 Sch 7 para 12. Westminster City Council publishes a "
        "2026-27 summary of its working-age scheme without the premium "
        "conditions, so the model assumes the Housing Benefit condition there. "
        "Oxford City Council sets "
        "its working-age award from income bands, so the premium does not "
        "reach it."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/1/paragraph/12/2021-04-01",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
        "https://www.merton.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%20L%20B%20Merton%202026-27.pdf",
        "https://www.kingston.gov.uk/sites/default/files/2026-03/Council%20Tax%20Reduction%20Scheme%202026%20-%202027.pdf",
        "https://www.newham.gov.uk/downloads/file/10753/council-tax-reduction-scheme-2026",
    )

    def formula(person, period, parameters):
        la = parameters(period).gov.local_authorities
        household = person.household
        country = household("country", period)
        local_authority = household("local_authority", period)
        under_age = ~person("has_attained_state_pension_credit_qualifying_age", period)

        def receives(benefits):
            return add(person, period, benefits) > 0

        def council_condition(council):
            p = council.council_tax_reduction.enhanced_disability_premium
            return receives(p.qualifying_benefits) & under_age

        p = la.scotland.council_tax_reduction.working_age.enhanced_disability_premium
        scottish = receives(p.qualifying_benefits) & (
            under_age | (not p.age_limit_applies)
        )
        housing_benefit = (
            person("receives_enhanced_disability_premium_qualifying_benefit", period)
            & under_age
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
