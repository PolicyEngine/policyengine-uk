from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import couple_members


class uc_youngest_child_age(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Age of the youngest child the Universal Credit claimants are responsible for"
    )
    documentation = (
        "The age of the youngest child in the benefit unit: a person under "
        "16 who normally lives with the claimants and is not looked after by "
        "a local authority. Infinite where there is no such child."
    )
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 40 (child: a person under the age of 16)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/40",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 4",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        ),
    ]
    definition_period = YEAR
    unit = "year"

    def formula(benunit, period, parameters):
        person = benunit.members
        # Reg. 4(2): a person is responsible for a child who normally lives
        # with them (here, a child in their benefit unit), but not for one
        # looked after by a local authority (reg. 4(6)(a)).
        child = (
            person("is_child_for_universal_credit", period)
            & ~person("is_looked_after_by_local_authority", period)
            & ~couple_members(person, period)
        )
        return benunit.min(where(child, person("age", period), np.inf))
