from policyengine_uk.model_api import *


class HousingBenefitPremisesCategory(Enum):
    NONE = "No temporary property category"
    ACQUIRED_HOME = "Acquired premises intended as home"
    SALE = "Premises being disposed of"
    LEGAL_POSSESSION = "Premises subject to steps for legal possession"
    ESSENTIAL_REPAIRS = "Premises requiring essential repairs before occupation"
    FORMER_HOME_ESTRANGEMENT = (
        "Former home left following estrangement/divorce/dissolution"
    )


class housing_benefit_capital_premises_category(Variable):
    value_type = Enum
    possible_values = HousingBenefitPremisesCategory
    default_value = HousingBenefitPremisesCategory.NONE
    entity = Person
    definition_period = YEAR
    label = "Temporary Housing Benefit property capital category"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
    )
