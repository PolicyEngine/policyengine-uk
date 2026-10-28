from policyengine_uk.model_api import *


class housing_benefit_permitted_work_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    default_value = 0
    label = "Pre-assessed Housing Benefit permitted-work earnings disregard"
    documentation = (
        "Annual amount legally disregarded under the permitted-work provision, "
        "before any lone-parent precedence and separate additional or "
        "accommodation disregard. The external assessor must establish "
        "qualifying benefit/credit status, exempt work, its statutory specified "
        "amount, and the earnings available for this deduction, including the "
        "partner allocation and limit. This is not gross permitted-work income "
        "or an unrestricted exemption of all earnings. Enter zero where the "
        "provision does not apply. No dataset mapping has been verified; the "
        "zero default retains the ordinary-disregard approximation and may "
        "understate qualifying awards. The model caps the supplied amount at "
        "net earnings but does not reconstruct permitted-work entitlement."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/10A",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/5A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/10A",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5/paragraph/5A",
    )
