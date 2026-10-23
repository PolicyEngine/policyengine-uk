import numpy as np


def net_income_from_adjusted_net_income(person, period, adjusted_net_income):
    """Restore the model's pre-allowance base from supplied s.58 ANI."""
    return (
        adjusted_net_income
        + person("gift_aid_grossed_up", period)
        + person("pension_contributions_relief", period)
    )


def calc_income_tax_with_gift_aid(
    scale, income, gross_gift, first_extended_threshold=1, last_extended_threshold=3
):
    """Apply ITA 2007 s.414(2)(b) to a per-person marginal-rate schedule.

    Moving a threshold t to t + G removes the rate step on the overlap
    with [t, t + G]. Summing those steps remains exact even when a gift
    spans several bands. Starting at index 2 leaves the Scottish starter
    band's upper limit unchanged. The default stop extends only the UK
    basic and higher limits, excluding the model's optional extra bracket.
    Scottish callers extend all subsequent limits. The scale is never mutated.
    https://www.legislation.gov.uk/ukpga/2007/3/section/414
    """
    tax = scale.calc(income)
    for index in range(
        first_extended_threshold, min(last_extended_threshold, len(scale.thresholds))
    ):
        overlap = np.clip(income - scale.thresholds[index], 0, gross_gift)
        tax = tax - (scale.rates[index] - scale.rates[index - 1]) * overlap
    return tax


def first_extended_scottish_threshold(scale):
    # The three-rate schedule before 2018 has no starter rate. Later
    # schedules have starter, basic, intermediate and higher rates.
    return 1 if len(scale.thresholds) == 3 else 2
