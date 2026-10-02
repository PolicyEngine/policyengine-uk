from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import is_on_relevant_benefit


class is_on_pawhp_relevant_benefit(Variable):
    value_type = bool
    entity = Person
    label = "on a relevant benefit for the Pension Age Winter Heating Payment"
    documentation = (
        "Whether this individual is entitled to a relevant benefit for the "
        "Pension Age Winter Heating Payment. The relevant benefits are listed "
        "in gov.social_security_scotland.pawhp.eligibility.relevant_benefits; "
        "for the 2024 qualifying week a tax credit award of at least £26 also "
        "counts (minimum_tax_credit_award). A member of a couple is treated "
        "as entitled when the other member is (SSI 2024/351 reg 7(2) as made, "
        "reg 10(8) as substituted by SSI 2025/282, and reg 2A from April "
        "2026), so the claimant and the partner are on it when their benefit "
        "unit's award is positive. Any other member of the benefit unit, such "
        "as a non-dependent adult, is on it only through their own award: "
        "their relevant benefit never counts for anyone else in the household."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/2",
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/7/made",
        "https://www.legislation.gov.uk/ssi/2025/282/regulation/9/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.social_security_scotland.pawhp.eligibility
        return is_on_relevant_benefit(person, period, p)
