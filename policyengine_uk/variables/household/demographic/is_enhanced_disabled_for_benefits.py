from policyengine_uk.model_api import *


class is_enhanced_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Receives an enhanced disability premium qualifying benefit (deprecated)"
    documentation = (
        "Deprecated: no premium reads it. The enhanced disability premium "
        "reads receives_enhanced_disability_premium_qualifying_benefit, which "
        "this returns, and applies each programme's own conditions. It is "
        "kept for downstream compatibility and for the deprecated counts "
        "num_enhanced_disabled_adults and num_enhanced_disabled_children. The "
        "Enhanced FRS stores its own value of this flag, which replaces this "
        "formula in dataset runs: attendance allowance at the higher rate, or "
        "disability living allowance care or personal independence payment "
        "daily living near the top rate, from reported amounts."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_enhanced_disability_premium_qualifying_benefit", period)
