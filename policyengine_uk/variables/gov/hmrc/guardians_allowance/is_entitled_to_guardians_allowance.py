from policyengine_uk.model_api import *


class is_entitled_to_guardians_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Entitled to Guardian's Allowance"
    documentation = (
        "Actual legal entitlement to Guardian's Allowance under section 77, "
        "established for this individual and the represented period. This "
        "asserts a valid claim, Child Benefit entitlement for the relevant "
        "child or qualifying young person, the prescribed parental and "
        "parental-connection conditions, and any applicable adoption or "
        "saved-claim rules. These facts are not inferred from household "
        "relationships, Child Benefit cash or a Guardian's Allowance payment. "
        "Record entitlement on its legal holder even when cash is nil or "
        "lawfully paid to someone else. The default does not establish "
        "that an unclassified person is legally ineligible."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/77",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/77",
        "https://www.legislation.gov.uk/uksi/2003/495",
        "https://www.legislation.gov.uk/uksi/2020/297/regulation/7/made",
        "https://www.legislation.gov.uk/uksi/2025/207/regulation/3/made",
        "https://www.legislation.gov.uk/uksi/2003/492/regulation/6",
    )
