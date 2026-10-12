from policyengine_uk.model_api import *


class uc_individual_earned_income_before_mif(Variable):
    value_type = float
    entity = Person
    label = (
        "Universal Credit earned income of the person, before the minimum income floor"
    )
    documentation = (
        "The person's actual earned income for Universal Credit: their "
        "earnings, including statutory sick, maternity and paternity pay, "
        "less their own relievable pension contributions and their own "
        "income tax and National Insurance in respect of their employment "
        "and self-employment. The minimum income floor compares this with "
        "the net threshold. Regulation 55(4) also treats statutory adoption, "
        "shared parental, parental bereavement and neonatal care pay as "
        "employed earnings; the model has no variables for those."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(4) and (5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Finance Act 2004 s. 188 (relievable pension contributions)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
        ),
    ]

    def formula(person, period, parameters):
        # The deductions are the person's own and come off only their own
        # earnings, so one partner's tax, NI or pension contributions never
        # reduce the other partner's earned income.
        # Miscellaneous income as income tax counts it, so a loss does not
        # reduce pay (and matches uc_income_tax_on_earnings). Whether it is
        # earnings at all is issue #1961.
        #
        # Reg. 55(4) treats statutory sick, maternity and paternity pay as
        # employed earnings, and reg. 55(5) takes the deductions off "the
        # amount of general earnings or benefits specified in paragraphs (2)
        # to (4)". National Insurance falls on all three (ni_class_1_income)
        # and income tax on sick and maternity pay (employment_benefits in
        # taxable_employment_income), and both are deducted below. Leaving
        # the payments out of the earnings deducted the tax and National
        # Insurance on them from other earnings, so the award rose as the
        # payments rose.
        earnings_components = [
            "employment_income",
            "taxable_miscellaneous_income",
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "statutory_paternity_pay",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            earnings_components.append("basic_income")
        # Reg. 57(2) nets the person's concurrent trades before the floor;
        # their loss never reduces employed earnings. Annual amounts assume
        # the trades' profits and losses accrue evenly across assessment periods.
        self_employed = max_(
            0,
            person("self_employment_income", period)
            - person("uc_trading_losses_set_against_profits", period),
        )
        earnings = add(person, period, earnings_components) + self_employed
        # Contributions paid after the person reaches 75 are not relievable
        # (Finance Act 2004 s. 188(3)(a)), so reg. 55(5)(a) does not deduct
        # them.
        age_limit = parameters(
            period
        ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        relievable_pension_contributions = person("pension_contributions", period) * (
            person("age", period) < age_limit
        )
        tax_and_national_insurance = add(
            person,
            period,
            ["uc_income_tax_on_earnings", "uc_national_insurance_on_earnings"],
        )
        return max_(
            0, earnings - relievable_pension_contributions - tax_and_national_insurance
        )
