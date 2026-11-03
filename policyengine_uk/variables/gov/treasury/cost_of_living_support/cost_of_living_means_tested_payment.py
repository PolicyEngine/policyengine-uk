from policyengine_uk.model_api import *


class cost_of_living_means_tested_payment(Variable):
    label = "Means-tested cost-of-living payment"
    documentation = (
        "The means-tested Cost of Living Payments to the benefit unit in the "
        "year. Under the Social Security (Additional Payments) Acts 2022 and "
        "2023 a person means an individual or a couple, so each benefit unit "
        "qualifies on its own. The Secretary of State pays a benefit unit "
        "with a qualifying benefit, and HMRC pays one with a qualifying tax "
        "credit and no qualifying benefit. In 2022-23 HMRC pays the tax "
        "credit route only where the yearly award of either credit reaches "
        "the minimum award."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/2022/38/section/1",
        "https://www.legislation.gov.uk/ukpga/2022/38/section/2",
        "https://www.legislation.gov.uk/ukpga/2023/7/section/1",
        "https://www.legislation.gov.uk/ukpga/2023/7/section/3",
    ]

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.treasury.cost_of_living_support.means_tested_households
        on_benefit = add(benunit, period, p.qualifying_benefits) > 0
        # The formula tests each credit's own award against the minimum,
        # following "the credit in question" in section 2(2) of the 2022 Act,
        # not the credits' sum.
        on_tax_credit = False
        for credit in p.qualifying_tax_credits:
            award = benunit(credit, period)
            on_tax_credit = on_tax_credit | (
                (award > 0) & (award >= p.minimum_tax_credit_award)
            )
        return p.amount * (on_benefit | on_tax_credit)
