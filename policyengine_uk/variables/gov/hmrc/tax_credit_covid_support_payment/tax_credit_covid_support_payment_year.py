from policyengine_uk.model_api import *


class tax_credit_covid_support_payment_year(Variable):
    value_type = int
    entity = BenUnit
    label = "Fiscal payment year of the one-off tax credit support payment"
    definition_period = YEAR
    default_value = 0
    documentation = (
        "Fiscal-year start of the single lawful Covid-19 tax-credit support "
        "payment for the historical claim represented by this benefit unit. "
        "Enter 2021 for 6 April 2021 to 5 April 2022, or 2022 for 6 April "
        "2022 to 5 April 2023. Initial-direction payments belong to 2021; "
        "extension payments can belong to 2021 or 2022. This is the payment "
        "year, not the 2020-21 qualifying-award year. Zero means no payment "
        "year has been established. Supply the same year in every requested "
        "model year so the single payment is not repeated. This fact alone "
        "does not establish entitlement: the corresponding verified "
        "historical eligibility fact is also required. The caller assigns "
        "one historical single or joint claim once; the model does not "
        "reconstruct changes in family composition."
    )
    reference = (
        "https://assets.publishing.service.gov.uk/media/606ee5ede90e076f4f581acd/WTC_Direction_060421.pdf#page=2",
        "https://www.gov.uk/government/publications/further-treasury-direction-made-under-section-76-of-the-coronavirus-act-2020/treasury-direction-made-under-section-76-of-the-coronavirus-act-2020",
    )
