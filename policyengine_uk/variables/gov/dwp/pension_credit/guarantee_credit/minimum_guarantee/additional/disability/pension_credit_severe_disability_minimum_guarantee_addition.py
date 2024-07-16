from policyengine_uk.model_api import *


class pension_credit_severe_disability_minimum_guarantee_addition(Variable):
    label = "Pension Credit severe disability-related increase"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1"
    )
    defined_for = "pension_credit_severe_disability_minimum_guarantee_addition_eligible"

    def formula(benunit, period, parameters):
        # 1. At least one adult receives a qualifying benefit
        # 2. No children (except children receiving qualifying benefits)
        # 3. Nobody receives Carer's Allowance (technically 'for one of the claimants', but we assume this is true)
        severe_disability = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability
        relevant_benefits = severe_disability.relevant_benefits
        person = benunit.members
        person_receives_qualifying_benefits = (
            add(person, period, relevant_benefits) > 0
        )
        is_adult = person("is_adult", period)
        count_eligible_adults = benunit.sum(
            is_adult & person_receives_qualifying_benefits
        )
        return (
            count_eligible_adults
            * severe_disability.amount
            * WEEKS_IN_YEAR
        )