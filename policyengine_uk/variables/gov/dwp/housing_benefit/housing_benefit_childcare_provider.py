from policyengine_uk.model_api import *


class HousingBenefitChildcareProvider(Enum):
    UNREGISTERED = "Unregistered or unknown provider"
    REGISTERED_APPROVED = (
        "Registered or approved under the applicable jurisdiction's prescribed scheme"
    )
    EXEMPT_SCHOOL = "School or establishment expressly exempt from registration"
    SCHOOL_LOCAL_AUTHORITY_OUT_OF_HOURS = "School or local authority out-of-hours route"
    FOSTER_KINSHIP_OTHER_CHILD = "Foster or kinship carer caring for a different child"
    DOMICILIARY_WORKER = "Prescribed domiciliary care worker"
    NON_RELATIVE_HOME_CARE = (
        "Non-relative providing care wholly or mainly in the child's home"
    )


class housing_benefit_childcare_provider(Variable):
    value_type = Enum
    possible_values = HousingBenefitChildcareProvider
    default_value = HousingBenefitChildcareProvider.UNREGISTERED
    entity = Person
    definition_period = YEAR
    label = "Housing Benefit provider caring for this child"
    documentation = "Statutory registration/approval or provider category for the care charged in respect of this child. The registered/exempt categories require the applicable GB or NI provision, not registration in another country. Other exclusion facts are tested separately. Unknown care does not automatically qualify."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/25",
    )
