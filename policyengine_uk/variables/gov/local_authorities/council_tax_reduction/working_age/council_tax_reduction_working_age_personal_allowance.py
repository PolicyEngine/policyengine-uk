from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_personal_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction personal allowance"
    documentation = (
        "Annual personal allowance in the applicable amount of a working-age "
        "applicant in Scotland or Wales. A couple and a lone parent get one "
        "rate at any age. A single applicant under 25 gets the lower rate "
        "unless entitled to main phase Employment and Support Allowance or, "
        "in Scotland, on Universal Credit with limited capability for work. "
        "Receipt of Employment and Support Allowance stands in for the main "
        "phase, and the model's limited-capability-for-work-related-activity "
        "flag for limited capability for work."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/1",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        country = benunit.household("country", period)
        scotland = is_scotland_scheme(country)
        scot = p.scotland.council_tax_reduction.working_age.personal_allowance
        wales = p.wales.council_tax_reduction.working_age.personal_allowance
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        age = benunit("eldest_claimant_or_partner_age", period)
        person = benunit.members
        claimant_or_partner = working_age_applicant_or_partner(person, period)
        on_esa = (
            add_for_members(
                benunit, period, ["esa_contrib", "esa_income"], claimant_or_partner
            )
            > 0
        )
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        limited_capability = benunit.any(
            claimant_or_partner & person("uc_limited_capability_for_WRA", period)
        )
        scotland_higher_single = (
            (age >= scot.age_threshold)
            | on_esa
            | (has_universal_credit & limited_capability)
        )
        wales_higher_single = (age >= wales.age_threshold) | on_esa
        scotland_single = where(
            scotland_higher_single, scot.single_25_or_over, scot.single_under_25
        )
        wales_single = where(
            wales_higher_single, wales.single_25_or_over, wales.single_under_25
        )
        scotland_amount = select(
            [couple, lone_parent], [scot.couple, scot.lone_parent], scotland_single
        )
        wales_amount = select(
            [couple, lone_parent], [wales.couple, wales.lone_parent], wales_single
        )
        pa = where(scotland, scotland_amount, wales_amount)
        return pa * WEEKS_IN_YEAR
