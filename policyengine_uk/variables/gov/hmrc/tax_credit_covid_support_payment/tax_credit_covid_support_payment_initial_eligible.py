from policyengine_uk.model_api import *


class tax_credit_covid_support_payment_initial_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Qualifying historical award for the initial tax credit support payment"
    definition_period = YEAR
    default_value = False
    documentation = (
        "Externally verified entitlement of the historical tax-credit claim "
        "represented by this benefit unit to the initial Covid-19 support "
        "payment. True asserts a current award for 2020-21 on 2 March 2021 "
        "of non-nil Working Tax Credit, or nil Working Tax Credit together "
        "with non-nil Child Tax Credit. It also asserts that the award was "
        "not terminated before that date under Tax Credits Act 2002 s.16, "
        "Universal Credit (Transitional Provisions) Regulations 2014 regs.8, "
        "46 or 47, or Childcare Payments Act 2014 s.30, and was not made "
        "non-payable under s.36A or s.36C for a period including that date. "
        "Neither the person nor either member of their couple obtained the "
        "award through knowing fraudulent involvement. These are supplied "
        "legal facts, not inferred from annual tax-credit income, current "
        "entitlement or a positive simulated award. Set this once per "
        "historical single or joint claim, not once per partner, and keep the "
        "fact consistent across payment years. The caller must map the "
        "historical claim to one benefit unit; the model does not reconstruct "
        "intervening separations or new couples. Initial entitlement prevents "
        "a second payment through the extension."
    )
    reference = "https://assets.publishing.service.gov.uk/media/606ee5ede90e076f4f581acd/WTC_Direction_060421.pdf#page=2"
