from policyengine_uk.model_api import *


class savings_credit_income(Variable):
    label = "Income for Savings Credit"
    documentation = (
        "Savings Credit (Pension Credit) excludes certain income sources of "
        "the claimant and partner from the calculation of the amount."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/9",
    )

    def formula(benunit, period, parameters):
        guarantee_credit_income = benunit("pension_credit_income", period)
        pc = parameters(period).gov.dwp.pension_credit
        person = benunit.members
        is_claimant_or_partner = person("is_claimant_or_partner", period)
        excluded_income = 0
        for source in pc.savings_credit.excluded_income:
            # Person-level sources count for the claimant and partner only;
            # benefit-unit sources (working tax credit) count once.
            if person.entity.get_variable(source).entity.is_person:
                excluded_income += benunit.sum(
                    person(source, period) * is_claimant_or_partner
                )
            else:
                excluded_income += add(benunit, period, [source])
        return max_(0, guarantee_credit_income - excluded_income)
