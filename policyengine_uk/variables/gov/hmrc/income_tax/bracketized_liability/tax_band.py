from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import first_extended_scottish_threshold


class TaxBand(Enum):
    NONE = "None"
    STARTER = "Starter (Scottish rates)"
    BASIC = "Basic"
    INTERMEDIATE = "Intermediate (Scottish rates)"
    HIGHER = "Higher"
    ADDITIONAL = "Additional"


def uk_tax_band_above_limits(person, period, parameters):
    """The rest-of-UK band before 2018-19: income above a limit is in the
    band above it."""
    allowances = person("allowances", period)
    ani = person("net_income", period)
    rates = parameters(period).gov.hmrc.income_tax.rates
    gross_gift = person("gift_aid_grossed_up", period)
    limits = [
        threshold + (gross_gift if index in (1, 2) else 0)
        for index, threshold in enumerate(rates.uk.thresholds)
    ]
    basic = allowances + limits[0]
    higher = allowances + limits[1]
    add = allowances + limits[2]
    return select(
        [ani > add, ani > higher, ani > basic],
        [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC],
        default=TaxBand.NONE,
    )


def scottish_tax_band(person, period, parameters):
    """The highest band in which a Scottish taxpayer has taxable income.

    Use the Scottish limits for income other than savings and dividends,
    the only income the Scottish rates charge (ITA 2007 s. 11A and the
    Scottish rate resolutions). Treat savings and dividends as the top
    slices of income (s. 16) and apply the rest-of-UK limits, since they
    bear the rates they would bear outside Scotland (ss. 11D(6) and 13(5)).
    Compare the rest-of-UK band only when taxable savings or dividends
    remain, then return the higher band. Keep income at each upper limit in
    the lower band: s. 10(2) to (3A) charges income "up to" a limit at the
    lower rate, and each resolution charges a rate "on income above" one
    limit "and up to" the next. As for every taxpayer, income charged at a
    nil rate stays in the band where it sits; the Marriage Allowance applies
    its own rate conditions (liable_only_at_marriage_allowance_rates).
    """
    rates = parameters(period).gov.hmrc.income_tax.rates
    gross_gift = person("gift_aid_grossed_up", period)
    scale = rates.scotland.rates
    if len(scale.thresholds) == 3:
        # 2017-18: the Scottish basic, higher and additional rates.
        scottish_bands = [TaxBand.BASIC, TaxBand.HIGHER, TaxBand.ADDITIONAL]
    else:
        # From 2018-19: the starter, basic, intermediate and higher rates,
        # then the top rate, which the advanced rate precedes from 2024-25.
        scottish_bands = [
            TaxBand.STARTER,
            TaxBand.BASIC,
            TaxBand.INTERMEDIATE,
            TaxBand.HIGHER,
        ] + [TaxBand.ADDITIONAL] * (len(scale.thresholds) - 4)
    labels = np.array([band.index for band in [TaxBand.NONE] + scottish_bands])
    # Allowances go to this income first, as in earned_income_tax. Marriage
    # Allowance is a tax reduction (s. 55B(1)), so it does not move the band.
    non_savings = person("non_savings_income_after_allowances", period)
    # s. 414(2)(b) raises the Scottish basic rate's upper limit and every
    # limit above it by the grossed-up gift.
    first_extended = first_extended_scottish_threshold(scale)
    limits_exceeded = sum(
        non_savings > threshold + (gross_gift if index >= first_extended else 0)
        for index, threshold in enumerate(scale.thresholds)
    )
    scottish_band = labels[limits_exceeded]
    uk_limits = rates.uk.thresholds
    taxable_income = person("net_income", period) - person("allowances", period)
    # Taxable income above the non-savings income is savings or dividends.
    # s. 414(2)(b) raises the basic and higher rate limits by the gift too.
    uk_band = select(
        [
            taxable_income <= non_savings,
            taxable_income > uk_limits[2] + gross_gift,
            taxable_income > uk_limits[1] + gross_gift,
        ],
        [TaxBand.NONE.index, TaxBand.ADDITIONAL.index, TaxBand.HIGHER.index],
        default=TaxBand.BASIC.index,
    )
    bands = np.array(list(TaxBand), dtype=object)
    return bands[max_(scottish_band, uk_band)]


class tax_band(Variable):
    value_type = Enum
    possible_values = TaxBand
    default_value = TaxBand.NONE
    entity = Person
    label = "Tax band of the individual"
    documentation = (
        "The highest band in which the person has taxable income. A "
        "Scottish taxpayer's band is the higher of the Scottish band of "
        "their income other than savings and dividends and the rest-of-UK "
        "band of their savings and dividends. Savings and dividends charged "
        "at a nil rate count where they sit. ADDITIONAL covers the Scottish "
        "advanced and top rates and the dividend additional rate; HIGHER "
        "covers the dividend upper rate."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007, s. 10",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
        ),
        dict(
            title="Income Tax Act 2007, s. 11A",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/11A",
        ),
        dict(
            title="Income Tax Act 2007, s. 13(5)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/13",
        ),
        dict(
            title="Scottish Rate Resolution 2025-26 (S6M-16531)",
            href="https://www.parliament.scot/chamber-and-committees/votes-and-motions/S6M-16531",
        ),
    ]

    def formula(person, period, parameters):
        return uk_tax_band_above_limits(person, period, parameters)

    def formula_2017(person, period, parameters):
        # Annual formulas start on 1 January, so this runs from 2017-18, the
        # first year of Scottish rates and limits.
        return where(
            person("pays_scottish_income_tax", period),
            scottish_tax_band(person, period, parameters),
            uk_tax_band_above_limits(person, period, parameters),
        )

    def formula_2018(person, period, parameters):
        allowances = person("allowances", period)
        ani = person("net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        income = ani - allowances
        gross_gift = person("gift_aid_grossed_up", period)
        # s.414(2)(b) extends the limits used to determine the tax band.
        uk_band = select(
            [
                income < threshold + (gross_gift if index > 0 else 0)
                for index, threshold in enumerate(rates.uk.thresholds[:3])
            ],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        return where(
            person("pays_scottish_income_tax", period),
            scottish_tax_band(person, period, parameters),
            uk_band,
        )
