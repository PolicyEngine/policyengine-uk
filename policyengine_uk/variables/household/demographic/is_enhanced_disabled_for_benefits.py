from policyengine_uk.model_api import *


class is_enhanced_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Receives an enhanced disability premium qualifying benefit (deprecated)"
    documentation = (
        "No premium reads this deprecated flag. The enhanced disability premium "
        "reads receives_enhanced_disability_premium_qualifying_benefit, which "
        "this returns, and applies each programme's own conditions. The model "
        "keeps it for downstream compatibility and for the deprecated counts "
        "num_enhanced_disabled_adults and num_enhanced_disabled_children. "
        "policyengine-uk-data stores its own value of this flag in the "
        "Enhanced FRS, and the model uses that value in place of this formula "
        "in dataset runs. The stored flag holds where reported attendance "
        "allowance reaches the higher weekly rate less £1, reported disability "
        "living allowance care exceeds the highest weekly rate less £1, or "
        "reported personal independence payment daily living reaches the "
        "enhanced weekly rate less £1."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_enhanced_disability_premium_qualifying_benefit", period)
