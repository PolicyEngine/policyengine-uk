from policyengine_uk.model_api import *


class forest_of_dean_council_tax_reduction_band_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Forest of Dean weekly income-band CTS rate"
    documentation = "Section 59 selects the entitlement percentage from the Class A or Class B six-band table based on the claimant and partner's weekly net income and household type (Single, Couple, Lone Parent or Couple with Children)."
    definition_period = YEAR
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.forest_of_dean.council_tax_reduction
        weekly_income = benunit(
            "forest_of_dean_council_tax_reduction_weekly_income", period
        )
        # Pad slightly so that exactly-on-the-boundary tests fall in the lower band.
        weekly_income_for_band = weekly_income + 1e-9
        is_couple = benunit("is_couple", period)
        is_lone_parent = benunit("is_lone_parent", period)
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_dependants = benunit.sum(child_or_young_person)
        has_children = num_dependants > 0
        protected = benunit(
            "forest_of_dean_council_tax_reduction_protected_group", period
        )
        non_protected_bands = ctr.income_band.non_protected
        protected_bands = ctr.income_band.protected
        non_protected_rate = select(
            [
                is_couple & has_children,
                is_couple,
                is_lone_parent,
            ],
            [
                non_protected_bands.couple_with_children.calc(weekly_income_for_band),
                non_protected_bands.couple.calc(weekly_income_for_band),
                non_protected_bands.lone_parent.calc(weekly_income_for_band),
            ],
            default=non_protected_bands.single.calc(weekly_income_for_band),
        )
        protected_rate = select(
            [
                is_couple & has_children,
                is_couple,
                is_lone_parent,
            ],
            [
                protected_bands.couple_with_children.calc(weekly_income_for_band),
                protected_bands.couple.calc(weekly_income_for_band),
                protected_bands.lone_parent.calc(weekly_income_for_band),
            ],
            default=protected_bands.single.calc(weekly_income_for_band),
        )
        return where(protected, protected_rate, non_protected_rate)
