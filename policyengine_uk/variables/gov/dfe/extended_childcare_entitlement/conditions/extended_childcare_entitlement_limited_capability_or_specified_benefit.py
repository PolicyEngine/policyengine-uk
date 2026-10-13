from policyengine_uk.model_api import *


class extended_childcare_entitlement_limited_capability_or_specified_benefit(Variable):
    value_type = bool
    entity = Person
    label = "limited capability for work or a specified benefit, for the extended childcare entitlement"
    documentation = (
        "Whether this person has limited capability for work, or for work and "
        "work-related activity, or is entitled to a specified benefit such as "
        "Carer's Allowance or Employment and Support Allowance (SI 2022/1134 "
        "regs 11A, 14(4)(b) and 15(4); SI 2016/1257 reg 9(1)(b) before "
        "1 December 2022). A parent or partner in this position meets the "
        "parent and partner conditions without the work or income conditions "
        "when the other meets them. A benefit-unit-level benefit in the list "
        "(income-related ESA) counts for both members of a couple; the "
        "Universal Credit carer element counts for the carer only. "
        "Income-related ESA is read as the claimant's and partner's award "
        "(claimant_or_partner_esa_income): another member of the benefit unit "
        "with an award of their own claims in their own right."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/11A",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/15",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.extended_childcare_entitlement
        criteria = list(p.disability_criteria)
        person_criteria = [
            variable
            for variable in criteria
            if person.entity.get_variable(variable).entity.is_person
        ]
        group_criteria = [
            variable
            for variable in criteria
            if not person.entity.get_variable(variable).entity.is_person
        ]
        meets_person_criteria = (
            add(person, period, person_criteria) > 0 if person_criteria else False
        )
        meets_group_criteria = (
            add(person.benunit, period, group_criteria) > 0 if group_criteria else False
        )
        return meets_person_criteria | meets_group_criteria
