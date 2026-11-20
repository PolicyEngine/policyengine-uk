from policyengine_uk.model_api import *


class armed_forces_independence_payment(Variable):
    label = "Armed Forces Independence Payment"
    documentation = (
        "Armed forces independence payment under article 24A of the Armed "
        "Forces and Reserve Forces (Compensation Scheme) Order 2011, payable "
        "to people with a guaranteed income payment at a relevant percentage "
        "of 50% or more. It is not part of afcs."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2011/517/article/24A"
