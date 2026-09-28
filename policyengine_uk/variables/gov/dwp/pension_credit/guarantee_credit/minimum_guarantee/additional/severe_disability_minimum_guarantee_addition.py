from policyengine_uk.model_api import *


class severe_disability_minimum_guarantee_addition(Variable):
    label = "Severe disability-related increase"
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
        # Count qualifying claimants/partners; children and qualifying young
        # people are ignored under Sch I para 2(2)(f).
        # Retained simplifications: one addition per qualifying member, without
        # para 1(1)(b)/(c)'s both-partners-or-blind-partner condition or the
        # household-level non-dependant residence test.
        # A carer benefit paid anywhere in the benefit unit is assumed to be
        # for a claimant and blocks the award. Underlying entitlement alone
        # does not block it; the person receiving care is not identified.
        severe_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability
        relevant_benefits = severe_disability.relevant_benefits
        person = benunit.members
        person_receives_qualifying_benefits = add(person, period, relevant_benefits) > 0
        claimant_or_partner = person("is_claimant_or_partner", period)
        count_eligible_claimants = benunit.sum(
            claimant_or_partner & person_receives_qualifying_benefits
        )
        carer_benefit_received = add(benunit, period, ["receives_carer_benefit"]) > 0
        return (
            ~carer_benefit_received
            * count_eligible_claimants
            * severe_disability.addition
            * WEEKS_IN_YEAR
        )
