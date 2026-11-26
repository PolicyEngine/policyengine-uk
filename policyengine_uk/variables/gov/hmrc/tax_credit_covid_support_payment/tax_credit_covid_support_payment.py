from policyengine_uk.model_api import *


class tax_credit_covid_support_payment(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax credit Covid-19 support payment"
    definition_period = YEAR
    default_value = 0
    unit = GBP
    documentation = (
        "The single lawful Covid-19 support payment for a historical "
        "tax-credit claim, separate from ordinary Working Tax Credit and "
        "Child Tax Credit. The benefit unit represents that historical "
        "single or joint claim once, so joint claimants share one payment. "
        "The initial/extension eligibility facts and selected fiscal payment "
        "year are supplied explicitly; annual tax-credit receipts and "
        "current-year entitlement do not establish them. Qualifying payments "
        "are exempt from income tax. This measure excludes recovery or tax "
        "charges on payments to which the recipient was not entitled and "
        "does not reconstruct historical family changes."
    )
    reference = (
        "https://assets.publishing.service.gov.uk/media/606ee5ede90e076f4f581acd/WTC_Direction_060421.pdf#page=2",
        "https://www.gov.uk/government/publications/further-treasury-direction-made-under-section-76-of-the-coronavirus-act-2020/treasury-direction-made-under-section-76-of-the-coronavirus-act-2020",
        "https://www.legislation.gov.uk/ukpga/2021/26/section/31/enacted",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.hmrc.tax_credit_covid_support_payment
        initial = benunit("tax_credit_covid_support_payment_initial_eligible", period)
        extension = benunit(
            "tax_credit_covid_support_payment_extension_eligible", period
        )
        payment_year = benunit("tax_credit_covid_support_payment_year", period)
        eligible = (initial & p.initial_scheme_in_effect) | (~initial & extension)
        return eligible * (payment_year == period.start.year) * p.amount
