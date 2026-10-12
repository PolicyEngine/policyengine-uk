from policyengine_uk.model_api import *


class would_claim_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "would claim Carer's Allowance"
    documentation = (
        "Whether this person would claim Carer's Allowance (or the Scottish "
        "Carer Support Payment) if entitled. Generated in a dataset from "
        "reported receipt so that caring hours can qualify a person as a carer "
        "for other benefits without paying the allowance to every carer; for "
        "the policy calculator it defaults to True."
    )
    definition_period = YEAR
    default_value = True
