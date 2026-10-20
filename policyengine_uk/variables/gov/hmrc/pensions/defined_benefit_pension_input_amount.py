from policyengine_uk.model_api import *


class defined_benefit_pension_input_amount(Variable):
    value_type = float
    entity = Person
    label = "Pension input amount under defined-benefit arrangements"
    documentation = (
        "The increase over the pension input period in the value of the "
        "individual's rights under defined-benefit arrangements (FA 2004 "
        "s. 234): 16 times the annual pension, plus any separate lump sum, at "
        "the end of the period less the same at its start, with the start "
        "value raised by CPI (s. 235), and nil if negative. Supply it where "
        "known, as on a scheme's pension savings statement. Otherwise it is "
        "defined_benefit_pension_contributions times "
        "gov.simulation.pensions.defined_benefit_input_per_contribution."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Finance Act 2004 s. 234",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/234",
        ),
        dict(
            title="Finance Act 2004 s. 235",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/235",
        ),
        dict(
            title="HMRC Pensions Tax Manual PTM053301",
            href="https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm053301",
        ),
    ]

    def formula(person, period, parameters):
        ratio = parameters(
            period
        ).gov.simulation.pensions.defined_benefit_input_per_contribution
        return ratio * person("defined_benefit_pension_contributions", period)
