from policyengine_uk.model_api import *


class tax_free_childcare(Variable):
    value_type = float
    entity = Person
    label = "government contribution through tax-free childcare"
    definition_period = YEAR
    unit = GBP
    defined_for = "tax_free_childcare_eligible"
    # Note: tax_free_childcare_eligible is a BenUnit variable implicitly cast to Person level

    def formula(person, period, parameters):
        # Get parameters
        tax_free_childcare = parameters(period).gov.hmrc.tax_free_childcare
        p = tax_free_childcare.contribution

        # Calculate per-person amounts
        is_disabled = person("is_disabled_for_benefits", period)
        is_blind = person("is_blind", period)
        is_qualifying_child = person("tax_free_childcare_qualifying_child", period)

        # Person gets higher amount if either disabled or blind
        qualifies_for_higher_amount = is_disabled | is_blind

        # Get childcare expenses
        childcare_expense = person("childcare_expenses", period)
        uses_qualifying_provider = person(
            "tax_free_childcare_uses_qualifying_provider", period
        )
        eligible_childcare_expense = childcare_expense * uses_qualifying_provider

        # Share of the year the family holds an eligible account. childcare_expenses
        # is an annual figure, so only this share of it is spent while eligible.
        eligible_periods = person.benunit(
            "tax_free_childcare_eligible_declaration_periods",
            period,
        )
        eligible_periods = min_(
            max_(eligible_periods, 0),
            tax_free_childcare.declaration_periods_per_year,
        )
        eligible_fraction = (
            eligible_periods / tax_free_childcare.declaration_periods_per_year
        )

        # Share of the year the account actually pays a provider. Eligibility
        # does not imply continuous use: HMRC's statistics show a claimant's
        # account pays a provider in about seven months of twelve, while
        # childcare_expenses is an annual figure. See
        # payment_active_fraction.yaml for the derivation and its source.
        active_fraction = tax_free_childcare.payment_active_fraction
        claimed_fraction = eligible_fraction * active_fraction

        # Calculate contribution using rate from parameters. The claimed share
        # applies to the spend, not only to the cap: a family claiming for half
        # the year puts roughly half its annual childcare spend through the
        # account, so it receives roughly half the top-up. Pro-rating the cap
        # alone left a part-year family below the cap with the full-year amount.
        contribution = (eligible_childcare_expense * claimed_fraction * p.rate) / (
            1 - p.rate
        )

        # The cap is statutorily per entitlement period, not per year, so a
        # period without payments forfeits that period's cap rather than
        # carrying it forward. It is pro-rated on the same basis.
        max_amount = (
            where(qualifies_for_higher_amount, p.disabled_child, p.standard_child)
            * is_qualifying_child
            * claimed_fraction
        )

        return min_(contribution, max_amount)
