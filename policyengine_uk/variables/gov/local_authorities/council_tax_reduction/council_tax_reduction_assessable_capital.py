from policyengine_uk.model_api import *


class council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "capital for the Council Tax Reduction capital limit"
    documentation = (
        "Capital tested against the Council Tax Reduction capital limit. The "
        "pensioner schemes disregard the whole capital of an applicant who, or "
        "whose partner, is in receipt of Pension Credit guarantee credit, and "
        "use the Secretary of State's Pension Credit assessment of capital where "
        "the award is savings credit only. Otherwise the household's capital "
        "stands in for the applicant's: savings, land and property other than "
        "the home (gov.local_authorities.council_tax_reduction.capital_sources). "
        "The schemes also count shares and other investments, but in the data "
        "those are mixed with pension wealth the schemes disregard, so they are "
        "left out for now. The recalculation when capital rises above the limit "
        "during an assessed income period is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/11",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/31",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/30",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
    ]

    def formula(benunit, period, parameters):
        in_receipt_of_guarantee_credit = benunit(
            "in_receipt_of_guarantee_credit", period
        )
        has_savings_credit_only_award = benunit(
            "in_receipt_of_savings_credit_only", period
        )
        sources = parameters(
            period
        ).gov.local_authorities.council_tax_reduction.capital_sources
        household_capital = sum(benunit.household(source, period) for source in sources)
        return select(
            [in_receipt_of_guarantee_credit, has_savings_credit_only_award],
            [0, benunit("pension_credit_assessable_capital", period)],
            default=household_capital,
        )
