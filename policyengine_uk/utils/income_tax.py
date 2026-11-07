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


def taxable_savings_income_in_band(
    person,
    period,
    income_tax,
    band_lower: np.ndarray | float,
    band_upper: np.ndarray | float,
) -> np.ndarray:
    """Allocate savings after the union of starting-rate and nil-rate slices.

    ITA 2007 s.12A places the savings nil rate above the starting-rate limit.
    For custom phase-out reforms, stack the nil slice after the actual
    starting-rate slice as well, preserving the full savings allowance.
    This stacking is a model convention for hypothetical reforms; s.12
    does not specify a phase-out. A higher reformed limit can still leave
    a taxable gap, and each relief is subtracted only once.
    https://www.legislation.gov.uk/ukpga/2007/3/section/12
    https://www.legislation.gov.uk/ukpga/2007/3/section/12A
    https://www.legislation.gov.uk/ukpga/2007/3/section/16
    """
    other_income = person("non_savings_taxable_income", period)
    savings_income = np.maximum(
        0,
        person("taxable_savings_interest_income", period)
        - person("received_allowances_savings_income", period),
    )
    savings_end = other_income + savings_income
    band_start = np.maximum(other_income, band_lower)
    band_end = np.minimum(savings_end, band_upper)
    starting_end = other_income + person("savings_starter_rate_income", period)
    starting_in_band = np.maximum(0, np.minimum(band_end, starting_end) - band_start)
    nil_start = np.maximum(
        np.maximum(other_income, income_tax.rates.savings_starter_rate.allowance),
        starting_end,
    )
    nil_end = np.minimum(savings_end, nil_start + person("savings_allowance", period))
    nil_in_band = np.maximum(
        0,
        np.minimum(band_end, nil_end)
        - np.maximum(band_start, np.maximum(nil_start, starting_end)),
    )
    return np.maximum(
        0, np.maximum(0, band_end - band_start) - starting_in_band - nil_in_band
    )
