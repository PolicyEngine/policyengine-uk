from policyengine_uk.model_api import *


class housing_benefit_non_dep_gross_income(Variable):
    """HB Regs 2006 reg 74(2) and pension-age reg 55(2) use "normal
    weekly gross income". Their reg 74(9) and reg 55(10) say "there shall
    be disregarded from his weekly gross income" the specified payments."""

    value_type = float
    entity = Person
    label = "Gross income for Housing Benefit non-dependant bands"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )
    documentation = (
        "Annual gross income the model represents for the non-dependant "
        "bands, before tax, National Insurance, employment deductions and "
        "pension contributions. DWP tells councils to count earnings and any "
        "other income (HB guidance A5.542), to count a self-employed "
        "non-dependant's total income before business expenses (A5.551) and "
        "to add savings interest to earnings (A5.570). The model holds "
        "self-employment and property profits rather than receipts, so it "
        "adds each profit and counts a loss as nil, and a loss never reduces "
        "other income. The claimant war-pension and supplementary-pension "
        "disregards do not apply to these bands. The total includes "
        "statutory sick, maternity and paternity pay once, through "
        "employment_benefits; child and spousal maintenance; the tax-purpose "
        "social security income sources; the non-taxable periodic benefits "
        "the model represents separately; and other investment income, ISA "
        "interest (tax_free_savings_income) and ISA dividends. It leaves out "
        "Attendance Allowance, DLA and PIP under the disability-payment "
        "disregards; the other disregarded disability, compensation and "
        "trust payments have no model inputs. BSP and AFCS inputs do not "
        "separate periodic income from capital payments, so the total leaves "
        "them out. Benefit-unit awards, such as Child Benefit, tax credits "
        "and Universal Credit, stay out of it. The deduction formula adds "
        "family awards to the claimant and partner's joint income and applies "
        "the remunerative-work test."
    )

    def formula(person, period, parameters):
        income = add(
            person,
            period,
            [
                "employment_income",
                "employment_benefits",
                "private_pension_income",
                "social_security_income",
                "savings_interest_income",
                # Count ISA interest unless the inputs supply an exempt-interest
                # total.
                "tax_free_savings_income",
                "other_investment_income",
                "dividend_income",
                "individual_savings_account_dividend_income",
                "miscellaneous_income_before_trading_allowance",
                "maternity_allowance",
                "iidb",
                "sda",
                "war_widows_pension",
            ],
        )
        # The model has profits, not the receipts DWP HB guidance A5.551
        # counts before business expenses. As an approximation, a loss
        # counts as nil, so it never reduces other income.
        losses_as_nil = max_(0, person("self_employment_income", period)) + max_(
            0, person("property_income", period)
        )
        return (
            income
            + losses_as_nil
            + max_(0, person("maintenance_income", period))
            + max_(0, person("spousal_maintenance_income", period))
        )
