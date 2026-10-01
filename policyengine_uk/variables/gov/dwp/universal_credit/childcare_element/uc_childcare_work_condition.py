from policyengine_uk.model_api import *


class uc_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets Universal Credit childcare work condition"
    documentation = (
        "Tests work for the claimant and partner, excluding dependants. "
        "The in_work proxy means positive hours or earnings; offers of work, "
        "the partner exceptions in regulation 32(1)(b), and the treated-as-working "
        "rules in regulation 32(2) are not modelled."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/32"

    def formula(benunit, period, parameters):
        # Reg. 32(1): "the claimant is in paid work" and, in a couple, "the
        # other member". Nobody else's work counts or is required.
        person = benunit.members
        claimant = person("is_uc_assessed_claimant", period)
        in_work = person("in_work", period)
        return benunit.any(claimant & in_work) & benunit.all(in_work | ~claimant)
