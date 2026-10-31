from policyengine_uk.model_api import *


class council_tax_reduction_non_dep_gross_income(Variable):
    """England SI 2012/2885 Sch 1 para 8(2) uses "normal gross weekly
    income"; para 8(9) says "there is to be disregarded from the
    non-dependent’s weekly gross income" the specified payments. Scotland
    and Wales also band gross income, with their own disregards."""

    value_type = float
    entity = Person
    label = "Gross income for Council Tax Reduction non-dependant bands"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
    )
    documentation = (
        "Annual gross income represented by the model for non-dependant "
        "bands, before tax, National Insurance, employment deductions and "
        "pension contributions. Signed trading/property inputs are retained; "
        "a separate cross-source loss-offset rule is not modelled. Claimant "
        "war-pension and supplementary-pension disregards do not apply to "
        "these non-dependant bands. It includes statutory sick, maternity and "
        "paternity pay once through employment_benefits, child and spousal "
        "maintenance, the tax-purpose social security income sources, and "
        "the separately represented non-taxable periodic benefits. "
        "Attendance Allowance, DLA and PIP are omitted under the specific "
        "disability-payment disregards. The other disregarded disability "
        "and compensation/trust payments have no separate model inputs. "
        "Benefit-unit awards (including Child Benefit, tax credits and UC) "
        "are not allocated to an individual recipient here; adding computed "
        "UC would also create a cycle through the benefit cap and HB. "
        "BSP and AFCS inputs do not separate periodic income from capital "
        "payments, so they are not added. Other investment income remains "
        "excluded to preserve this income base; extending it remains for "
        "#2007. The deduction formula applies the remunerative-work gate. The "
        "gross-income variable itself does not decide whether someone is "
        "in remunerative work or whether a deduction is due."
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
                "self_employment_income",
                "property_income",
                "savings_interest_income",
                "dividend_income",
                "miscellaneous_income_before_trading_allowance",
                "maternity_allowance",
                "iidb",
                "sda",
                "war_widows_pension",
            ],
        )
        return (
            income
            + max_(0, person("maintenance_income", period))
            + max_(0, person("spousal_maintenance_income", period))
        )
