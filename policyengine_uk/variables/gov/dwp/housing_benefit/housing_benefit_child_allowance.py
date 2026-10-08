from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class housing_benefit_child_allowance(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit child personal allowances"
    documentation = "Child personal allowances, with actual CTC-award and continuing-child transitional protection during the two-child restriction. Missing award/history facts default to no exception, not an inferred award. Jurisdiction-specific changes are day-weighted over the fiscal year, holding supplied family facts fixed."
    reference = (
        "https://www.legislation.gov.uk/uksi/2017/376/made",
        "https://www.legislation.gov.uk/nisr/2017/79/made",
        "https://www.legislation.gov.uk/uksi/2024/611/regulation/6",
        "https://www.legislation.gov.uk/nisr/2024/119/regulation/5",
        "https://www.legislation.gov.uk/uksi/2026/316/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/68/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/22",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/22",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        p = parameters(period).gov.dwp.housing_benefit.allowances
        child = person("is_child_or_young_person_for_legacy_benefits", period)
        count = benunit.sum(child)
        protected = benunit.sum(
            child
            & person("housing_benefit_child_in_family_at_two_child_limit_start", period)
        )
        continuing_claim = (
            benunit("housing_benefit_entitled_at_two_child_limit_start", period)
            & (
                benunit("housing_benefit_child_count_at_two_child_limit_start", period)
                > p.child_limit.count
            )
            & ~benunit("housing_benefit_new_claim_since_two_child_limit_start", period)
        )
        protected_count = where(continuing_claim, protected, 0)
        restricted_count = min_(
            count,
            max_(
                p.child_limit.count,
                max_(
                    protected_count,
                    max_(0, benunit("housing_benefit_ctc_child_element_count", period)),
                ),
            ),
        )
        country = benunit.household("country", period)
        ni = country == country.possible_values.NORTHERN_IRELAND
        pension = benunit("housing_benefit_pension_age_regulations_apply", period)
        total = 0
        for rules, share in fiscal_year_segments(
            parameters.gov.dwp.housing_benefit.allowances.child_limit.schedule,
            period.start.year,
        ):
            applies = where(
                ni,
                where(pension, rules.ni_pension_age, rules.ni_working_age),
                where(pension, rules.gb_pension_age, rules.gb_working_age),
            )
            total += (
                where(applies, restricted_count, count)
                * p.child
                * WEEKS_IN_YEAR
                * share
            )
        return total
