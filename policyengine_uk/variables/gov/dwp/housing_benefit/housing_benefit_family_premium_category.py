from policyengine_uk.model_api import *


class HousingBenefitFamilyPremiumCategory(Enum):
    ORDINARY_PROTECTED = "Ordinary protected family premium"
    HISTORICAL_LONE_PARENT_PROTECTED = "Protected pre-April 1998 lone-parent premium"
    NONE = "No protected family premium"


class housing_benefit_family_premium_category(Variable):
    value_type = Enum
    possible_values = HousingBenefitFamilyPremiumCategory
    default_value = HousingBenefitFamilyPremiumCategory.NONE
    entity = BenUnit
    definition_period = YEAR
    label = "Pre-assessed Housing Benefit protected family premium category"
    documentation = (
        "Legally assessed family-premium protection, including continuous "
        "qualifying entitlement before GB's 1 May 2016 or NI's 5 September "
        "2016 new-claim closure and subsequent loss-of-protection conditions. "
        "The historical lone-parent category additionally requires the "
        "pre-April 1998 continuity conditions, not current lone-parent status "
        "alone. It applies only in the working-age schedule. No dataset "
        "mapping has been verified: NONE from the closure year omits "
        "protected awards and can understate entitlement. This annual "
        "pre-assessment does not reconstruct changes within the year."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/2/2015-04-06",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/part/II/2015-04-06",
    )
