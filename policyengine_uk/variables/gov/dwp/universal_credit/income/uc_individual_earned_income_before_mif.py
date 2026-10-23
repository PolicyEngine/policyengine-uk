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
        "less allowable employment expenses, their own relievable pension contributions and their own "
        "income tax and National Insurance in respect of their employment "
        "and self-employment. Concurrent trade results include company "
        "income treated as self-employed earnings under regulation 77; "
        "losses and trade-only tax and NI never reduce employed earnings. "
        "The minimum income floor compares this with the net threshold. "
        "Regulation 55(4) also treats statutory adoption, "
        "shared parental, parental bereavement and neonatal care pay as "
        "employed earnings; the model has no variables for those."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(3)(a), (4) and (5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations (Northern Ireland) 2016 reg. 55(3)(a)",
            href="https://www.legislation.gov.uk/nisr/2016/216/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 77(3)(b) and (4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
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
        # Self-employed earnings follow reg. 57(2): each trade's profit or
        # loss is added together (step 2), including a company's income
        # treated as the owner's self-employed earnings (reg. 77(3)(b)),
        # less concurrent trading losses. The income tax and National
        # Insurance paid in respect of any trade come off that total
        # (step 3) before a nil or negative result
        # becomes nil. So a trading loss, or tax on a trade a company loss
        # has cancelled, is never set against employed earnings.
        trade = (
            person("self_employment_income", period)
            + person("uc_company_self_employed_earnings", period)
            - person("uc_trading_losses_set_against_profits", period)
            - person("uc_income_tax_on_trade", period)
            - person("uc_national_insurance_on_trade", period)
        )
        self_employed = max_(0, trade)
        # Employed earnings less the income tax and primary Class 1
        # contributions paid in respect of the employment (reg. 55(5)(b)).
        employment_tax_and_national_insurance = (
            person("uc_income_tax_on_earnings", period)
            - person("uc_income_tax_on_trade", period)
            + person("uc_national_insurance_on_earnings", period)
            - person("uc_national_insurance_on_trade", period)
        )
        # Reg. 55(3)(a) disregards expenses allowed under Chapter 2 of
        # Part 5 ITEPA. This input is the already-allowable amount, after
        # relevant-employment limits, not a claim for arbitrary raw costs.
        employed = (
            add(person, period, earnings_components)
            - person("employment_expenses", period)
            - employment_tax_and_national_insurance
        )
        # Contributions paid after the person reaches 75 are not relievable
        # (Finance Act 2004 s. 188(3)(a)), so reg. 55(5)(a) does not deduct
        # them. Reg. 55(5)(a) takes them off employed earnings and reg.
        # 57(2) step 4 off what is left of self-employed earnings.
        age_limit = parameters(
            period
        ).gov.hmrc.pensions.pension_contributions_relief_age_limit
        relievable_pension_contributions = person("pension_contributions", period) * (
            person("age", period) < age_limit
        )
        return max_(0, employed + self_employed - relievable_pension_contributions)
