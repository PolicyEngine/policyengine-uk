from policyengine_uk.model_api import *


class targeted_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for targeted childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check if household is in England
        country = benunit.household("country", period)
        in_england = country == country.possible_values.ENGLAND

        # Get benunit's income excluding social security
        total_income = benunit.sum(benunit.members("total_income", period))
        social_security_income = benunit.sum(
            benunit.members("social_security_income", period)
        )
        adjusted_income = total_income - social_security_income

        # Check Universal Credit eligibility
        uc = benunit("universal_credit", period)
        max_uc_income = p.max_income_uc_recipients
        meets_uc = (uc > 0) & (adjusted_income <= max_uc_income)

        # Check Tax Credits eligibility
        tax_credits = add(
            benunit, period, ["child_tax_credit", "working_tax_credit"]
        )
        meets_tc = (tax_credits > 0) & (
            total_income <= p.max_income_tc_recipients
        )

        # Check other qualifying benefits
        has_qualifying_benefits = (
            add(benunit, period, p.qualifying_benefits) > 0
        )

        # Determine overall benefits eligibility
        return where(
            uc > 0,
            meets_uc,
            where(tax_credits > 0, meets_tc, has_qualifying_benefits),
        ) & in_england