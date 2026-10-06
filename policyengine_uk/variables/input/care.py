from policyengine_uk.model_api import *

label = "Care"


class receives_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "receives Carer's Allowance"
    documentation = "Whether this person receives Carer's Allowance."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carers_allowance", period) > 0


class receives_carer_support_payment(Variable):
    value_type = bool
    entity = Person
    label = "receives Carer Support Payment"
    documentation = "Whether this person receives Carer Support Payment."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carer_support_payment", period) > 0


class receives_carer_benefit(Variable):
    value_type = bool
    entity = Person
    label = "receives a carer benefit"
    documentation = (
        "Whether this person receives Carer's Allowance or the Scottish "
        "Carer Support Payment."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_carers_allowance", period) | person(
            "receives_carer_support_payment", period
        )


class is_entitled_to_carer_benefit(Variable):
    value_type = bool
    entity = Person
    label = "entitled to a carer benefit"
    documentation = (
        "Whether this person is entitled to Carer's Allowance or the Scottish "
        "Carer Support Payment, whether or not it is paid. An overlapping "
        "benefit such as State Pension can reduce the payment to nil and leave "
        "this underlying entitlement in place."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/12",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
    )

    def formula(person, period, parameters):
        entitlements = add(
            person,
            period,
            ["carers_allowance_pre_overlap", "carer_support_payment_pre_overlap"],
        )
        # A carer benefit supplied directly as an input is also an entitlement.
        return (entitlements > 0) | person("receives_carer_benefit", period)
