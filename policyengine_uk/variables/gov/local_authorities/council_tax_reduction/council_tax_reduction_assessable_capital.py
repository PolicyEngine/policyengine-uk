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
        "the award is savings credit only. Otherwise household savings stand in "
        "for the applicant's capital; the schemes' own capital rules also count "
        "other property and investments, so this understates capital for "
        "pensioners without Pension Credit. The recalculation when capital rises "
        "above the limit during an assessed income period is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/11",
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
        return select(
            [in_receipt_of_guarantee_credit, has_savings_credit_only_award],
            [0, benunit("pension_credit_assessable_capital", period)],
            default=benunit.household("savings", period),
        )
