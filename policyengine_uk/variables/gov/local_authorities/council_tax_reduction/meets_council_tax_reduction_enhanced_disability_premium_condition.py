from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class meets_council_tax_reduction_enhanced_disability_premium_condition(Variable):
    value_type = bool
    entity = Person
    label = "Meets the working-age CTR enhanced disability premium condition"
    documentation = (
        "Whether this person, as an applicant or partner, meets the enhanced "
        "disability premium condition of the working-age Council Tax "
        "Reduction scheme that covers their household. In Scotland the "
        "scheme's own list of qualifying benefits applies, which adds "
        "attendance allowance at either rate from 1 April 2023, and the age "
        "limit applies only until 20 June 2022. Elsewhere the condition is "
        "Housing Benefit's: a qualifying benefit (receives_enhanced_"
        "disability_premium_qualifying_benefit) and not having attained the "
        "qualifying age for State Pension Credit, as in the Welsh scheme and "
        "England's Default Scheme. The English councils' own schemes have not "
        "been checked against this. England's Default Scheme names the PIP "
        "daily living component at either rate and does not name armed forces "
        "independence payment, which the model does not follow."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/1/paragraph/12/2021-04-01",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2012/2886/appendix/3/paragraph/12",
    )

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.working_age.enhanced_disability_premium
        scotland = is_scotland_scheme(person.household("country", period))
        under_age = ~person("has_attained_state_pension_credit_qualifying_age", period)
        scottish = (add(person, period, p.qualifying_benefits) > 0) & (
            under_age | ~p.age_limit_applies
        )
        elsewhere = (
            person("receives_enhanced_disability_premium_qualifying_benefit", period)
            & under_age
        )
        return where(scotland, scottish, elsewhere)
