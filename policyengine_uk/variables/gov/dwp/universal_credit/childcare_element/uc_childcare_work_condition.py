from policyengine_uk.model_api import *


class uc_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets Universal Credit childcare work condition"
    documentation = (
        "Tests work for the claimant and partner, excluding dependants. "
        "The in_work proxy means positive hours or earnings; offers of work, "
        "the partner exceptions in regulation 32(1)(b), and the treated-as-working "
        "rules in regulation 32(2) are not modelled. Where a member of a "
        "couple claims as a single person (regulation 3(3)), the claimant must "
        "be in work and the other member is tested as a partner is, "
        'regulation 32(1)(b) applying "whether claiming jointly or as a '
        'single person".'
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/32"

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant = person("is_uc_single_or_joint_claimant", period)
        claimant_or_partner = person("is_uc_claimant", period)
        in_work = person("in_work", period)
        return benunit.any(claimant & in_work) & benunit.all(
            in_work | ~claimant_or_partner
        )
