from policyengine_uk.model_api import *


class meets_tax_credit_criteria_for_targeted_childcare_entitlement(Variable):
    value_type = bool
    entity = BenUnit
    label = "meets Tax Credit criteria for targeted childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        tax_credits = add(
            benunit, period, ["child_tax_credit", "working_tax_credit"]
        )

        tax_credits_applicable_income = benunit(
            "tax_credits_applicable_income", period
        )

        # Check Tax Credits eligibility
        # Legislation source for total (applicable) income limit:The Local Authority Regulations 2014, part 1.2.b
        # https://www.legislation.gov.uk/uksi/2014/2147/regulation/1/made

        # Reference for applicable income: The Tax Credits (Definition and Calculation of Income) Regulations 2002 s. 3

        return (tax_credits > 0) & (
            tax_credits_applicable_income <= p.income_limit.tax_credits
        )
