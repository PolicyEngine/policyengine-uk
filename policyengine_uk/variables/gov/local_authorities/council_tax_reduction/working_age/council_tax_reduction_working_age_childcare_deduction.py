from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_childcare_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction childcare charges deduction"
    documentation = (
        "Annual relevant childcare charges deducted from a working-age "
        "applicant's income in Scotland or Wales. Without Universal Credit, "
        "childcare spending is deducted from earnings after the earnings "
        "disregards (never below zero), up to a weekly cap for "
        "one child or for two or more, where a lone parent, or both members "
        "of a couple, are in remunerative work. A Scottish applicant with "
        "Universal Credit deducts the Universal Credit childcare costs element "
        "grossed up to the full cost, up to higher caps. A Welsh applicant "
        "with Universal Credit uses the Secretary of State's income figure, "
        "which has no childcare deduction. The number of children in the "
        "family stands in for the number with childcare charges, and the "
        "incapacity, hospital and prison cases for couples are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/38",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/42",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/77",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/78",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/20",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/21",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        scot = p.scotland.council_tax_reduction.working_age
        wales = p.wales.council_tax_reduction.working_age
        scotland = is_scotland_scheme(benunit.household("country", period))
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        children = benunit.sum(
            person("is_child_or_young_person_for_legacy_benefits", period)
        )
        two_or_more = children >= 2
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        # Without Universal Credit: charges paid, capped, where the lone parent
        # or both members of the couple are in remunerative work.
        hours_threshold = where(
            scotland,
            scot.earnings_disregard.remunerative_work_hours,
            wales.earnings_disregard.remunerative_work_hours,
        )
        in_work = person("weekly_hours", period) >= benunit.project(hours_threshold)
        all_claimants_in_work = benunit.sum(claimant_or_partner & ~in_work) == 0
        charges = benunit.sum(person("childcare_expenses", period))
        weekly_cap = where(
            scotland,
            where(
                two_or_more,
                scot.childcare.maximum_two_or_more_children,
                scot.childcare.maximum_one_child,
            ),
            where(
                two_or_more,
                wales.childcare.maximum_two_or_more_children,
                wales.childcare.maximum_one_child,
            ),
        )
        legacy = where(
            (children > 0) & all_claimants_in_work,
            min_(charges, weekly_cap * WEEKS_IN_YEAR),
            0,
        )
        # Scotland, with Universal Credit: the childcare costs element grossed
        # up to the full charge.
        uc_charges = benunit("uc_childcare_element", period) / (
            scot.childcare.universal_credit_costs_covered
        )
        uc_weekly_cap = where(
            two_or_more,
            scot.childcare.universal_credit_maximum_two_or_more_children,
            scot.childcare.universal_credit_maximum_one_child,
        )
        scotland_uc = min_(uc_charges, uc_weekly_cap * WEEKS_IN_YEAR)
        return where(
            has_universal_credit,
            where(scotland, scotland_uc, 0),
            legacy,
        )
