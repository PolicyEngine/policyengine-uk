from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import (
    calc_income_tax_with_gift_aid,
    first_extended_scottish_threshold,
)
from policyengine_uk.variables.household.demographic.country import Country

# Taxable non-savings income other than earnings. Scotland's working-age scheme
# deducts no tax from it.
NON_EARNINGS_NON_SAVINGS_INCOME = [
    "taxable_pension_income",
    "taxable_social_security_income",
    "taxable_property_income",
    "taxable_miscellaneous_income",
]
# Taxable non-savings income that the pensioner schemes do not take into
# account: the Scottish Carer Supplement (SSI 2012/319 reg 27(1)(j)(xxib)),
# miscellaneous income and benefits in kind, which the model's Council Tax
# Reduction income does not count.
PENSIONER_UNCOUNTED_NON_SAVINGS_INCOME = [
    "scottish_carer_supplement",
    "taxable_miscellaneous_income",
    "benefits_in_kind",
]
# National Insurance charged on earnings and profits. Class 3 contributions are
# voluntary and not charged on earnings.
NATIONAL_INSURANCE_ON_EARNINGS = ["ni_class_1_employee", "ni_class_2", "ni_class_4"]


def tax_below_top_slice(person, period, parameters, top_slice):
    """Step 5 tax on a person's non-savings income without its top slice.

    Savings and dividend income are taxed as the highest part of income, so
    the Step 5 tax on the rest is earned_income_tax plus property_income_tax.
    The top_slice of non-savings income is taken as the highest part of the
    non-savings income, and its tax at the person's main rates is taken off.
    Allowances and reliefs therefore fall on the income below it, and that
    income keeps the personal allowance it would have on its own: the part of
    the allowance withdrawn only because the top slice, savings and dividends
    lift adjusted net income above the taper threshold is restored to it.
    """
    allowance = parameters(period).gov.hmrc.income_tax.allowances.personal_allowance
    rates = parameters(period).gov.hmrc.income_tax.rates
    non_savings_tax = add(person, period, ["earned_income_tax", "property_income_tax"])
    taxable = person("non_savings_taxable_income", period)
    income_above = top_slice + add(
        person, period, ["taxable_savings_interest_income", "taxable_dividend_income"]
    )
    income_below = max_(0, person("adjusted_net_income", period) - income_above)
    allowance_alone = max_(
        0,
        np.ceil(
            allowance.amount
            - max_(0, income_below - allowance.maximum_ANI) * allowance.reduction_rate
        ),
    )
    restored_allowance = max_(0, allowance_alone - person("personal_allowance", period))
    below = max_(0, taxable - top_slice - restored_allowance)
    gross_gift = person("gift_aid_grossed_up", period)
    scottish = rates.scotland.rates
    first_extended = first_extended_scottish_threshold(scottish)
    scottish_bands = len(scottish.thresholds)

    def tax_at_main_rates(income):
        return where(
            person("pays_scottish_income_tax", period),
            calc_income_tax_with_gift_aid(
                scottish, income, gross_gift, first_extended, scottish_bands
            ),
            calc_income_tax_with_gift_aid(rates.uk, income, gross_gift),
        )

    tax_on_top_slice = max_(0, tax_at_main_rates(taxable) - tax_at_main_rates(below))
    # With no taxable income below the top slice there is no tax on it; this
    # also clears the rounding left by the subtraction.
    return where(below > 0, max_(0, non_savings_tax - tax_on_top_slice), 0)


def tax_after_reductions_and_charges(person, period, step_5_part):
    """Income Tax attributed to a part of the Step 5 tax.

    The Step 6 reductions come off that part first, as they would if it were
    the person's only income. The Step 7 charges other than the winter fuel
    payment charge are shared in proportion to the part's share of the Step 5
    tax. The result never exceeds income_tax_before_winter_fuel_payment_charge.
    """
    step_5_tax = max_(0, person("income_tax_pre_charges", period))
    reductions = person("income_tax_reductions", period)
    charges = person("income_tax_charges", period)
    share = np.divide(
        step_5_part,
        step_5_tax,
        out=np.zeros_like(step_5_tax),
        where=step_5_tax > 0,
    )
    return max_(0, step_5_part - reductions) + charges * min_(share, 1)


class council_tax_reduction_tax_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction deduction for income tax and National Insurance"
    documentation = (
        "Income tax and National Insurance that Council Tax Reduction income "
        "deducts, for the applicant and partner "
        "(is_council_tax_reduction_applicant_or_partner). Scotland's "
        "working-age scheme (SSI 2021/249) deducts them from earnings only, "
        "so the formula deducts National Insurance on earnings and profits "
        "(Classes 1, 2 and 4) and the Income Tax on earnings, taken as the "
        "Step 5 tax that employment and self-employment income bear as the "
        "lowest part of non-savings income, with the other non-savings "
        "income above them and savings and dividends taxed separately. The "
        "pensioner schemes of England (SI 2012/2885), Wales (WSI 2013/3029) "
        "and Scotland (SSI 2012/319) disregard tax only on income taken into "
        "account, so the formula deducts the same National Insurance and the "
        "Step 5 tax on non-savings income less the tax on the Scottish Carer "
        "Supplement, miscellaneous income and benefits in kind, taken as the "
        "highest part of non-savings income. The income below keeps the "
        "personal allowance it would have on its own. Tax on savings and dividend "
        "income is never deducted in these schemes. In each, the Step 6 tax "
        "reductions come off the tax deducted first, and the Step 7 charges "
        "other than the winter fuel payment charge are shared in proportion "
        "to the Step 5 tax. The ordering of earnings below other non-savings "
        "income is a modelling choice: the regulations name the tax deducted "
        "from earnings, not a way to apportion it. The English and Welsh "
        "working-age schemes, and families outside Great Britain, deduct the "
        "whole Income Tax liability before the winter fuel payment charge "
        "and all National Insurance."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/49",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/50",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/51",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/31",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/11",
    ]

    def formula(benunit, period, parameters):
        person = benunit.members
        members = person("is_council_tax_reduction_applicant_or_partner", period)
        country = benunit.household("country", period)
        in_great_britain = (
            (country == Country.ENGLAND)
            | (country == Country.SCOTLAND)
            | (country == Country.WALES)
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        scottish_working_age = (country == Country.SCOTLAND) & ~pensioner
        pensioner_scheme = in_great_britain & pensioner

        whole_tax = add(
            person,
            period,
            ["income_tax_before_winter_fuel_payment_charge", "national_insurance"],
        )
        ni_on_earnings = add(person, period, NATIONAL_INSURANCE_ON_EARNINGS)
        earnings_step_5_tax = tax_below_top_slice(
            person,
            period,
            parameters,
            add(person, period, NON_EARNINGS_NON_SAVINGS_INCOME),
        )
        counted_step_5_tax = tax_below_top_slice(
            person,
            period,
            parameters,
            add(person, period, PENSIONER_UNCOUNTED_NON_SAVINGS_INCOME),
        )
        tax_on_earnings = (
            tax_after_reductions_and_charges(person, period, earnings_step_5_tax)
            + ni_on_earnings
        )
        tax_on_counted_income = (
            tax_after_reductions_and_charges(person, period, counted_step_5_tax)
            + ni_on_earnings
        )
        person_scottish_working_age = benunit.project(scottish_working_age)
        person_pensioner_scheme = benunit.project(pensioner_scheme)
        deduction = select(
            [person_scottish_working_age, person_pensioner_scheme],
            [tax_on_earnings, tax_on_counted_income],
            default=whole_tax,
        )
        return benunit.sum(deduction * members)
