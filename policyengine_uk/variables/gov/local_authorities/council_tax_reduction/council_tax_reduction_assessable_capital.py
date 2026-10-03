from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


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
        "credit only. Where the applicant or partner has an award of Universal "
        "Credit, the working-age schemes use the Secretary of State's "
        "assessment of capital for that award (uc_assessable_capital), except "
        "the Scottish scheme from April 2022, under which the authority "
        "calculates capital itself. Otherwise the household's capital stands "
        "in for the applicant's: savings, land and property other than the "
        "home (gov.local_authorities.council_tax_reduction.capital.sources), "
        "with land and property valued at market value less 10% for the "
        "expenses of sale. The schemes also deduct any encumbrance secured on "
        "an asset, which the data cannot identify for property other than the "
        "home, and count shares and other investments, which in the data are "
        "mixed with pension wealth the schemes disregard; both are left out "
        "for now. The recalculation when capital rises above the limit during "
        "an assessed income period is not modelled."
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
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/70",
    ]

    def formula(benunit, period, parameters):
        in_receipt_of_guarantee_credit = benunit(
            "in_receipt_of_guarantee_credit", period
        )
        has_savings_credit_only_award = benunit(
            "in_receipt_of_savings_credit_only", period
        )
        # SI 2012/2886 Sch para 37(6), WSI 2013/3029 Sch 6 para 9(6) and SSI
        # 2012/303 reg 26: with an award of Universal Credit, the authority
        # uses the Secretary of State's calculation of capital. SSI 2021/249
        # has no such rule.
        p_scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.means_test
        scotland = is_scotland_scheme(benunit.household("country", period))
        uses_universal_credit_assessment = ~scotland | (
            p_scotland.uses_universal_credit_capital_assessment
        )
        has_uc_award = benunit("universal_credit", period) > 0
        p = parameters(period).gov.local_authorities.council_tax_reduction.capital
        # Capital is valued at market value less 10% where there would be
        # expenses of sale (SI 2012/2885 Sch 1 para 32(a) and equivalents).
        household_capital = 0
        for source in p.sources:
            value = benunit.household(source, period)
            if source in p.sale_expenses.sources:
                value = value * (1 - p.sale_expenses.rate)
            household_capital = household_capital + value
        return select(
            [
                in_receipt_of_guarantee_credit,
                has_savings_credit_only_award,
                has_uc_award & uses_universal_credit_assessment,
            ],
            [
                0,
                benunit("pension_credit_assessable_capital", period),
                benunit("uc_assessable_capital", period),
            ],
            default=household_capital,
        )
