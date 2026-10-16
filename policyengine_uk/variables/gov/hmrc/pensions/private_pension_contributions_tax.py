from policyengine_uk.model_api import *


def _top_slice_charge(bottom, top, thresholds, rates, extension):
    """Tax on the slice from ``bottom`` to ``top`` of income, at ``rates``
    between ``thresholds``, every limit above the first raised by
    ``extension``."""
    charge = 0
    for i, rate in enumerate(rates):
        lower = thresholds[i] + (extension if i > 0 else 0)
        upper = thresholds[i + 1] + extension if i + 1 < len(thresholds) else np.inf
        charge = charge + rate * max_(0, min_(top, upper) - max_(bottom, lower))
    return charge


class personal_pension_contributions_tax(Variable):
    value_type = float
    entity = Person
    label = "Pension annual allowance charge"
    documentation = (
        "The annual allowance charge (FA 2004 s. 227) on the chargeable amount, "
        "the pension input amount above the annual allowance. It is charged at "
        "the basic, higher and additional rates on the slices of the chargeable "
        "amount that fall in each band when it is added to the top of the "
        "individual's reduced net income, their income after allowances "
        "(s. 227(4A)-(4B)), with gross Gift Aid extending rate limits. "
        "Relieved relief-at-source contributions extend limits only where "
        "ordinary income, before that relief, meets s. 192(4)/(4A)'s "
        "above-basic-rate condition (s. 227(4C)/(5)). A Scottish "
        "taxpayer pays the Scottish rates, with the Scottish basic rate on any "
        "slice within the Scottish basic rate limit (s. 227(4AA)). "
        "Personal contribution relief has a separate earnings limit "
        "(pension_contributions_relief); the annual allowance does not "
        "also deny that relief."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 192",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/192",
        ),
        dict(
            title="Finance Act 2004 s. 227",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/227",
        ),
        dict(
            title="Income Tax Act 2007 s. 58",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/58",
        ),
        dict(
            title="Finance Act 2004 s. 233",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/233",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        rates = income_tax.rates
        chargeable_amount = person("pension_annual_allowance_chargeable_amount", period)
        # FA 2004 s. 227(4B)-(4C): relief at source remains in reduced net
        # income. It raises rate limits only if s. 192's condition is met.
        # The model includes
        # that relief in allowances, so restore it at Step 3. Net pay
        # contributions stay deducted. Gift Aid is already excluded from
        # allowances; only its gross amount extends the limits (ITA 2007
        # s. 414(2)), without another deduction from the taxable base.
        relief_at_source = min_(
            person("personal_pension_contributions", period),
            person("pension_contributions_relief", period),
        )
        gross_gift = person("gift_aid_grossed_up", period)
        allowances_at_step_3 = max_(
            0,
            person("allowances", period) - relief_at_source,
        )
        # Reduced net income is income after ITA 2007 s. 23 Step 3, not
        # adjusted net income after the s. 58 gross Gift Aid deduction.
        reduced_net_income = max_(
            0, person("net_income", period) - allowances_at_step_3
        )
        top_of_charge = reduced_net_income + chargeable_amount

        # s. 192(4): test ordinary liability apart from RAS relief, with
        # Gift Aid's limits still extended. s. 227(5) excludes the pension
        # excess itself. Dividends have separate rates and cannot satisfy
        # the higher/additional-rate condition; savings at a nil rate cannot
        # satisfy it either. Retain the model's fixed allowance allocation.
        savings = person("taxable_savings_interest_income", period)
        dividends = person("taxable_dividend_income", period)
        non_savings = max_(0, reduced_net_income - savings - dividends)
        savings_top = max_(0, reduced_net_income - dividends)
        savings_after_allowances = savings_top - non_savings
        savings_amounts = income_tax.allowances.personal_savings_allowance
        savings_allowance_without_ras = select(
            [
                reduced_net_income > rates.uk.thresholds[2] + gross_gift,
                reduced_net_income > rates.uk.thresholds[1] + gross_gift,
            ],
            [savings_amounts.additional, savings_amounts.higher],
            default=savings_amounts.basic,
        )
        nil_rate_savings = min_(
            savings_after_allowances,
            savings_allowance_without_ras
            + max_(0, rates.savings_starter_rate.allowance - non_savings),
        )
        uk_basic_limit = rates.uk.thresholds[1] + gross_gift
        uk_ras_condition = (non_savings > uk_basic_limit) | (
            savings_top > max_(uk_basic_limit, non_savings + nil_rate_savings)
        )

        uk_charge = _top_slice_charge(
            reduced_net_income,
            top_of_charge,
            list(rates.uk.thresholds),
            list(rates.uk.rates),
            gross_gift + relief_at_source * uk_ras_condition,
        )

        # s. 227(4AA)(b)(i): no slice is charged at the starter rate. The
        # Scottish basic rate applies to every slice up to the Scottish basic
        # rate limit, so charge the starter band at the basic rate. The
        # starter bracket (the first) is null before 2018-19, when the lowest
        # Scottish rate was the basic rate; it is present only with both a
        # rate and a threshold.
        scottish_rates = rates.scotland.rates
        scottish_band_rates = list(scottish_rates.rates)
        starter_bracket = person.simulation.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.scotland.rates.brackets[
            0
        ]
        has_starter_band = (
            starter_bracket.rate(period.start) is not None
            and starter_bracket.threshold(period.start) is not None
            and len(scottish_band_rates) > 1
        )
        if has_starter_band:
            scottish_band_rates[0] = scottish_band_rates[1]
        # s. 192(4A): only non-savings income is charged at Scottish rates.
        # The first rate above basic is intermediate from 2018, higher before.
        scottish_ras_condition = False
        for threshold, rate in zip(scottish_rates.thresholds, scottish_band_rates):
            if rate > scottish_band_rates[0]:
                scottish_ras_condition = scottish_ras_condition | (
                    non_savings > threshold + gross_gift
                )
        scottish_charge = _top_slice_charge(
            reduced_net_income,
            top_of_charge,
            list(scottish_rates.thresholds),
            scottish_band_rates,
            gross_gift + relief_at_source * scottish_ras_condition,
        )

        return where(
            person("pays_scottish_income_tax", period),
            scottish_charge,
            uk_charge,
        )
