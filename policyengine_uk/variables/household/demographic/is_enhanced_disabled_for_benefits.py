from policyengine_uk.model_api import *


class is_enhanced_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether meets the middle disability benefit entitlement"
    documentation = (
        "The model reads this flag for the enhanced disability premium in "
        "Kingston upon Thames's working-age Council Tax Reduction, with no age "
        "limit (meets_council_tax_reduction_enhanced_disability_premium_condition), "
        "and in the deprecated counts num_enhanced_disabled_adults and "
        "num_enhanced_disabled_children. No other premium reads it. The formula "
        "holds where DLA care reaches 52 times the highest weekly rate. "
        "policyengine-uk-data stores its own value of this flag in the Enhanced "
        "FRS, and the model uses that value in place of the formula in dataset "
        "runs. The stored flag holds where reported attendance allowance "
        "reaches the higher weekly rate less £1, reported disability living "
        "allowance care exceeds the highest weekly rate less £1, or reported "
        "personal independence payment daily living reaches the enhanced weekly "
        "rate less £1. Issue #2881 lists what the model needs to apply Kingston "
        "upon Thames's own list."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        DLA_requirement = (
            parameters(period).gov.dwp.dla.self_care.higher * WEEKS_IN_YEAR
        )
        return person("dla_sc", period) >= DLA_requirement
