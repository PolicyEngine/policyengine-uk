from policyengine_uk.model_api import *


class housing_benefit_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit tariff income from capital"
    documentation = "Weekly Housing Benefit tariff income from capital annualised to the model period."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/52",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/26",
    )

    def formula(benunit, period, parameters):
        capital = benunit("housing_benefit_assessable_capital", period)
        # The pension tariff applies "For the purposes of these Regulations"
        # (SI 2006/214 reg 29(2)); SI 2006/213 reg 52 supplies the working tariff.
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        guarantee_credit = pension_age_regulations & (
            benunit("guarantee_credit", period) > 0
        )
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        threshold = where(
            pension_age_regulations,
            p.pension_age.tariff_income.threshold,
            p.working_age.tariff_income.threshold,
        )
        step = where(
            pension_age_regulations,
            p.pension_age.tariff_income.step,
            p.working_age.tariff_income.step,
        )
        amount = where(
            pension_age_regulations,
            p.pension_age.tariff_income.amount,
            p.working_age.tariff_income.amount,
        )
        excess_capital = max_(0, capital - threshold)
        steps = np.ceil(excess_capital / step)
        tariff_income = steps * amount * WEEKS_IN_YEAR
        # SI 2006/214 reg 27(5) (NI: SR 2006/406 reg 25(5)): where the award of
        # Pension Credit is savings credit only, Housing Benefit's tariff
        # income rule does not apply; the Secretary of State's assessment of
        # income already counts Pension Credit deemed income from capital.
        # That regulation is in the pension-age regulations, so it applies only
        # where they do.
        savings_credit_only = pension_age_regulations & benunit(
            "in_receipt_of_savings_credit_only", period
        )
        tariff_income = where(savings_credit_only, 0, tariff_income)
        return where(guarantee_credit, 0, tariff_income)
