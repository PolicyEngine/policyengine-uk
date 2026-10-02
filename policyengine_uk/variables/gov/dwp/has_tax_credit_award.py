from policyengine_uk.model_api import *


class has_tax_credit_award(Variable):
    value_type = bool
    entity = BenUnit
    label = "has a tax credit award"
    documentation = (
        "Whether the family is awarded child tax credit or working tax credit "
        "for the year, at any rate. Entitlement depends on a claim (TCA 2002 "
        "s.3(1)), which a couple makes jointly (s.3(3)(a)), so an award is "
        "both members'. On a claim HMRC decide whether to make an award and "
        "at what rate (s.14(1)), and may award a tax credit at a nil rate "
        "(s.14(3)). So the award follows the claim and the conditions of "
        "entitlement other than the income test, not a positive amount. Tax "
        "credits ended on 5 April 2025, so there are no awards after that."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/14",
    )

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.tax_credits.active:
            return benunit.filled_array(False)
        # Neither condition reads Pension Credit, which reads this award
        # (child_minimum_guarantee_addition), so no cycle arises.
        child_tax_credit = benunit("would_claim_CTC", period) & benunit(
            "is_CTC_eligible", period
        )
        working_tax_credit = benunit("would_claim_WTC", period) & benunit(
            "is_WTC_eligible", period
        )
        return child_tax_credit | working_tax_credit
