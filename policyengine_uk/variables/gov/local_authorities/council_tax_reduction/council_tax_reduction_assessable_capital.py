from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
    is_wales_scheme,
)

# The debt input secured on each capital source. The schemes deduct "the
# amount of any encumbrance secured on it" from that asset after the sale
# expenses, so a source is never valued below nil and negative equity in one
# source does not reduce another. Land has no secured-debt input.
SECURED_DEBT = {
    "other_residential_property_value": "other_residential_property_secured_debt",
    "non_residential_property_value": "non_residential_property_secured_debt",
}


class council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "capital for the Council Tax Reduction capital limit"
    documentation = (
        "Capital tested against the Council Tax Reduction capital limit and "
        "used for tariff income. The pensioner schemes disregard the whole "
        "capital of an applicant who, or whose partner, is in receipt of "
        "Pension Credit guarantee credit, and use the Secretary of State's "
        "Pension Credit assessment of capital where the award is savings "
        "credit only. Where an applicant who is not a pensioner, or their "
        "partner, has an award of Universal Credit "
        "(council_tax_reduction_universal_credit_award, which includes an "
        "award the benefit cap or deductions reduce to nil), the schemes use "
        "the Secretary of State's assessment of capital for that award "
        "(uc_assessable_capital), except the Scottish scheme from April 2022, "
        "under which the authority calculates capital itself. The Welsh "
        "scheme, and the Scottish scheme before April 2022, disregard the "
        "whole capital of an applicant on Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance; the English local schemes that do the same apply it in "
        "their own formulas. Otherwise the household's capital stands in for "
        "the applicant's: savings, land and property other than the home "
        "(gov.local_authorities.council_tax_reduction.capital.sources), with "
        "land and property valued at market value less 10% for the expenses "
        "of sale, then less any debt secured on that property (which defaults "
        "to nil because the survey does not record it). The schemes also "
        "count shares and other investments, which in the data are mixed "
        "with pension wealth the schemes disregard, so they are left out for "
        "now. The recalculation when capital rises above the limit during an "
        "assessed income period is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/11",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/31",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/32",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/37",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/30",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/26",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/10/paragraph/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/5/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/70",
    ]

    def formula(benunit, period, parameters):
        # The benefit unit's Pension Credit is its claimant's and partner's, not
        # a household head's who applies alone
        # (council_tax_reduction_head_applies_alone).
        applicant_family = ~benunit("council_tax_reduction_head_applies_alone", period)
        in_receipt_of_guarantee_credit = applicant_family & benunit(
            "in_receipt_of_guarantee_credit", period
        )
        has_savings_credit_only_award = applicant_family & benunit(
            "in_receipt_of_savings_credit_only", period
        )
        country = benunit.household("country", period)
        scotland = is_scotland_scheme(country)
        wales = is_wales_scheme(country)
        p_scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.means_test
        working_age = ~benunit("council_tax_reduction_pensioner", period)
        # SI 2012/2886 Sch para 37(6), WSI 2013/3029 Sch 6 para 9(6) and SSI
        # 2012/303 reg 26: with an award of Universal Credit, the authority
        # uses the Secretary of State's calculation of capital. These are
        # working-age rules. SSI 2021/249 has no such rule.
        uses_universal_credit_assessment = ~scotland | (
            p_scotland.uses_universal_credit_capital_assessment
        )
        universal_credit_route = (
            working_age
            & benunit("council_tax_reduction_universal_credit_award", period)
            & uses_universal_credit_assessment
        )
        # WSI 2013/3029 Sch 10 para 8 and SSI 2012/303 Sch 5 para 7: the whole
        # capital of an applicant on Income Support, income-based JSA or
        # income-related ESA is disregarded. SSI 2021/249 has no such
        # disregard: reg 13(11) treats only the income conditions as met.
        passported = working_age & benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        disregards_passported_capital = wales | (
            scotland & p_scotland.disregards_passported_applicants_capital
        )
        p = parameters(period).gov.local_authorities.council_tax_reduction.capital
        # Capital is valued at market value less 10% where there would be
        # expenses of sale, then less any encumbrance secured on it (SI
        # 2012/2885 Sch 1 para 32 and equivalents).
        household_capital = 0
        for source in p.sources:
            value = max_(0, benunit.household(source, period))
            if source in p.sale_expenses.sources:
                value = value * (1 - p.sale_expenses.rate)
            if source in SECURED_DEBT:
                debt = max_(0, benunit.household(SECURED_DEBT[source], period))
                value = max_(0, value - debt)
            household_capital = household_capital + value
        return select(
            [
                in_receipt_of_guarantee_credit,
                has_savings_credit_only_award,
                universal_credit_route,
                passported & disregards_passported_capital,
            ],
            [
                0,
                benunit("pension_credit_assessable_capital", period),
                benunit("uc_assessable_capital", period),
                0,
            ],
            default=household_capital,
        )
