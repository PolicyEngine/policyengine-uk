from policyengine_uk.model_api import *


class uc_minimum_income_floor_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor deduction for income tax"
    documentation = (
        "The amount for income tax deducted from the person's gross "
        "individual threshold to give their net minimum income floor. The "
        "regulations leave it to the Secretary of State; the model takes the "
        "income tax the person would pay if the threshold were their only "
        "income: the threshold less the standard personal allowance, at the "
        "person's own rest-of-UK or Scottish rates."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 62(4)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
        dict(
            title="Advice for Decision Making, chapter H4, H4078-H4079",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]

    def formula(person, period, parameters):
        # Reg. 62(4)(b) deducts "such amount for income tax ... as the
        # Secretary of State considers appropriate". The model treats the
        # threshold as the person's only income: only the standard personal
        # allowance applies, and no other allowance or relief.
        income_tax = parameters(period).gov.hmrc.income_tax
        threshold = person("uc_minimum_income_floor_gross", period)
        taxable = max_(0, threshold - income_tax.allowances.personal_allowance.amount)
        return where(
            person("pays_scottish_income_tax", period),
            income_tax.rates.scotland.rates.calc(taxable),
            income_tax.rates.uk.calc(taxable),
        )
