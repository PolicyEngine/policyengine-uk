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
        "(s. 227(4A)-(4B)), with the rate limits raised by relief-at-source "
        "contributions and grossed-up Gift Aid (s. 227(4C)). A Scottish "
        "taxpayer pays the Scottish rates, with the Scottish basic rate on any "
        "slice within the Scottish basic rate limit (s. 227(4AA)). "
        "Contributions above the annual allowance still get relief "
        "(pension_contributions_relief), so the charge recovers that relief "
        "once rather than taxing the excess twice."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 227",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/227",
        ),
        dict(
            title="Finance Act 2004 s. 233",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/233",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        chargeable_amount = person("pension_annual_allowance_chargeable_amount", period)
        # The model deducts relief at source (personal pension contributions)
        # and Gift Aid from income, where the law leaves them in reduced net
        # income and raises the rate limits instead (s. 227(4C); FA 2004
        # s. 192(4), ITA 2007 s. 414). Undo the deduction and raise the
        # limits, as capital_gains_tax does for the basic rate band. Net pay
        # contributions stay deducted, as in law.
        relief_at_source = min_(
            person("personal_pension_contributions", period),
            person("pension_contributions_relief", period),
        )
        rate_limit_extension = person("gift_aid_grossed_up", period) + relief_at_source
        allowances_at_step_3 = max_(
            0,
            person("allowances", period)
            - person("gift_aid", period)
            - relief_at_source,
        )
        # Reduced net income: income after Step 3 of ITA 2007 s. 23 (s. 227(4B)).
        reduced_net_income = max_(
            0, person("adjusted_net_income", period) - allowances_at_step_3
        )
        top_of_charge = reduced_net_income + chargeable_amount

        uk_charge = _top_slice_charge(
            reduced_net_income,
            top_of_charge,
            list(rates.uk.thresholds),
            list(rates.uk.rates),
            rate_limit_extension,
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
        scottish_charge = _top_slice_charge(
            reduced_net_income,
            top_of_charge,
            list(scottish_rates.thresholds),
            scottish_band_rates,
            rate_limit_extension,
        )

        return where(
            person("pays_scottish_income_tax", period),
            scottish_charge,
            uk_charge,
        )
