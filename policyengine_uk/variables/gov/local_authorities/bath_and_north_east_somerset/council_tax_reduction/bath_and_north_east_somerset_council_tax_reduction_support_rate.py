from policyengine_uk.model_api import *


class bath_and_north_east_somerset_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Bath and North East Somerset Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.bath_and_north_east_somerset.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        protected = benunit(
            "bath_and_north_east_somerset_council_tax_reduction_protected_group",
            period,
        )
        ordinary_non_uc_rate = where(
            protected, ctr.protected_maximum_support_rate, ctr.maximum_support_rate
        )
        weekly_income = benunit(
            "bath_and_north_east_somerset_council_tax_reduction_uc_weekly_income",
            period,
        )
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        child_count = min_(2, benunit.sum(child_or_young_person))
        adjusted_income = max_(
            0,
            weekly_income - child_count * ctr.income_band.child_increment,
        )
        # The source bands are printed to the penny with inclusive upper bounds.
        # Nudge after rounding so 98.05 stays in band 1 and 98.06 enters band 2.
        band_income = adjusted_income + 0.001
        uc_rate = where(
            benunit("is_couple", period),
            ctr.income_band.couple.support_rate.calc(band_income),
            ctr.income_band.single.support_rate.calc(band_income),
        )
        return where(has_uc_award, uc_rate, ordinary_non_uc_rate)
