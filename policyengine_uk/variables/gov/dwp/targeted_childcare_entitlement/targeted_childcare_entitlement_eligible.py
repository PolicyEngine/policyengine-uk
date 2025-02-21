from policyengine_uk.model_api import *


class targeted_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligibility for targeted childcare entitlement based on benefits"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check country eligibility first
        country = benunit.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND

        # Check qualifying benefits
        qualifying_benefits = add(benunit, period, p.qualifying_benefits)

        # Universal Credit check
        uc = benunit("universal_credit", period)
        uc_income = benunit.sum(
            benunit.members("total_income", period)
        ) - benunit.sum(benunit.members("social_security_income", period))
        meets_uc = (uc > 0) & (uc_income <= p.max_income_for_universal_credit)

        # Tax Credits check
        tc = add(benunit, period, ["child_tax_credit", "working_tax_credit"])
        meets_tc = (tc > 0) & (
            benunit.sum(benunit.members("total_income", period))
            <= p.max_income_for_tax_credits
        )

        return (
            where(
                uc > 0,
                meets_uc,
                where(tc, meets_tc, qualifying_benefits > 0),
            )
            & in_england
        )
