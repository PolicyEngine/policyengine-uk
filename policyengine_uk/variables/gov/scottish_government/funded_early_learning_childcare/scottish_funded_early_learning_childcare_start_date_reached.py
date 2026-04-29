from policyengine_uk.model_api import *


class scottish_funded_early_learning_childcare_start_date_reached(Variable):
    value_type = bool
    entity = Person
    label = "has reached the Scottish funded early learning and childcare start date"
    documentation = (
        "Whether this child has reached the statutory start date for Scottish "
        "funded early learning and childcare. For 3-year-olds, entitlement "
        "starts at the beginning of the first term after the child's 3rd "
        "birthday. This is captured as an input because annual age alone does "
        "not identify the relevant birthday and local term dates."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.gov.scot/publications/early-learning-childcare-statutory-guidance-july-2021/pages/8/"
