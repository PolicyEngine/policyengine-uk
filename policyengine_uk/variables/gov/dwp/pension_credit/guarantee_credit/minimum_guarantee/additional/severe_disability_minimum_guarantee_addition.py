from policyengine_uk.model_api import *


class severe_disability_minimum_guarantee_addition(Variable):
    label = "Severe disability-related increase"
    documentation = (
        "The Pension Credit severe disability additional amount: one rate for "
        "each adult in the benefit unit who receives a qualifying disability "
        "benefit and for whom no other member of the benefit unit receives a "
        "carer benefit. Pension-age Housing Benefit and Council Tax Reduction "
        "use the same amount as their severe disability premium."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        # Sch I para 1(1)(a)(iii) and (b): the addition is withheld where a
        # person is entitled to and in receipt of a carer benefit "in respect
        # of caring for" the qualifying person. Who is cared for is not
        # modelled, so another member of the benefit unit receiving a carer
        # benefit stands in for it; a person's own carer benefit never blocks
        # their addition, and carers outside the benefit unit are not seen.
        # Receipt, not underlying entitlement, is what counts.
        # Children and qualifying young people never block the addition: the
        # residence test counts only people aged 18 or over, and para 2(2)(f)
        # ignores qualifying young people.
        # Retained simplifications: one rate for each qualifying adult,
        # without para 1(1)(b)-(c)'s both-partners-or-blind-partner condition,
        # and no test for other adults living in the household.
        severe_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability
        person = benunit.members
        qualifies = add(person, period, severe_disability.relevant_benefits) > 0
        receives_carer_benefit = person("receives_carer_benefit", period)
        carer_benefits_received_by_others = (
            benunit.project(benunit.sum(receives_carer_benefit))
            - receives_carer_benefit
        )
        counted = (
            person("is_adult", period)
            & qualifies
            & (carer_benefits_received_by_others == 0)
        )
        return benunit.sum(counted) * severe_disability.addition * WEEKS_IN_YEAR
