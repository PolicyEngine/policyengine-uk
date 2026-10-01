from policyengine_uk.model_api import *


def _take(amount, band_left):
    """Fill a rate band from one schedule's gains.

    Returns the part inside the band, the part above it and the band left for
    the next schedule. The "above" expression subtracts the whole band, as the
    single-schedule formula did, so a schedule that is the only one with gains
    reproduces that formula bit for bit.
    """
    inside = min_(amount, band_left)
    above = max_(amount - band_left, 0)
    return inside, above, band_left - inside


class capital_gains_tax(Variable):
    label = "capital gains tax"
    documentation = (
        "Capital gains tax on the person's gains, charged on four schedules: "
        "gains qualifying for Business Asset Disposal Relief or Investors' "
        "Relief (capital_gains_badr, a flat rate up to the lifetime limit), "
        "residential property gains (capital_gains_residential_property), "
        "carried interest (capital_gains_carried_interest) and the remainder of "
        "capital_gains at the main rates. The three named inputs are components "
        "of capital_gains, scaled by any realisation response, and are clipped so "
        "that together they never exceed it. The annual exempt amount is set "
        "against the schedule with the highest top rate first (TCGA 1992 "
        "s. 1K(5)); the unused basic rate band goes to relief gains first, as "
        "s. 1I(4)-(6) requires, and then to the schedule with the widest gap "
        "between its higher and basic rates (s. 1I(7)-(9)). Gains above the "
        "basic rate band are split at the income tax higher rate limit only so "
        "that reforms can set an additional rate; the law has none."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "Taxation of Chargeable Gains Act 1992 ss. 1H-1K, 169N"

    def formula(person, period, parameters):
        hmrc = parameters(period).gov.hmrc
        cgt = hmrc.cgt
        it = hmrc.income_tax

        personal_pension_band_extension = min_(
            person("personal_pension_contributions", period),
            person("pension_contributions_relief", period),
        )
        basic_rate_band_extension = (
            person("gift_aid_grossed_up", period) + personal_pension_band_extension
        )
        allowances_for_cgt_income = max_(
            0,
            person("allowances", period)
            - person("gift_aid", period)
            - personal_pension_band_extension,
        )
        taxable_income = max_(
            0,
            person("adjusted_net_income", period) - allowances_for_cgt_income,
        )
        capital_gains = person("capital_gains", period)
        gains = max_(0, capital_gains)
        aea = cgt.annual_exempt_amount
        basic_rate_limit = it.rates.uk.thresholds[1] + basic_rate_band_extension
        remaining_basic_rate_band = max_(basic_rate_limit - taxable_income, 0)
        higher_rate_limit = it.rates.uk.thresholds[2] + basic_rate_band_extension
        higher_rate_band = higher_rate_limit - basic_rate_limit

        # The schedule inputs describe gains before any realisation response.
        # Scale them by realised over pre-response gains so a response, or a
        # marginal pound added to capital_gains directly, is shared across the
        # schedules in proportion to their shares. Then clip each against what
        # is left of the realised gains so inconsistent inputs cannot exceed
        # the total; the remainder is charged at the main rates.
        before_response = person("capital_gains_before_response", period)
        has_before_response = before_response > 0
        ratio = where(
            has_before_response,
            capital_gains / where(has_before_response, before_response, 1),
            1,
        )

        def component(variable):
            return max_(0, person(variable, period) * ratio)

        badr = min_(
            min_(component("capital_gains_badr"), cgt.badr.lifetime_limit), gains
        )
        residential = min_(
            component("capital_gains_residential_property"), gains - badr
        )
        carried = min_(
            component("capital_gains_carried_interest"),
            gains - badr - residential,
        )
        main = gains - badr - residential - carried

        # Band schedules in declaration order, which also breaks ties below.
        rates = {
            "carried_interest": cgt.carried_interest,
            "residential_property": cgt.residential_property,
            "main": cgt,
        }
        amounts = {
            "carried_interest": carried,
            "residential_property": residential,
            "main": main,
            "badr": badr,
        }
        top_rate = {name: rates[name].higher_rate for name in rates}
        top_rate["badr"] = cgt.badr.rate

        # Annual exempt amount, TCGA 1992 s. 1K(5): deducted in the way most
        # beneficial to the taxpayer, which is against the highest top rate
        # first. Relief gains carry the lowest rate and come last.
        after_aea = {}
        aea_left = aea
        for name in sorted(amounts, key=lambda name: -top_rate[name]):
            used = min_(amounts[name], aea_left)
            after_aea[name] = amounts[name] - used
            aea_left = aea_left - used

        # Basic rate band. Relief gains take it first, TCGA 1992 s. 1I(4)-(6).
        # The taxpayer then allocates the rest, s. 1I(7)-(9), which saves most
        # on the schedule with the widest higher-minus-basic gap. Carried
        # interest from 2025-26 has no gap and comes last, matching its
        # exclusion from the band by Finance Act 2025 s. 12.
        basic_order = ["badr"] + sorted(
            rates,
            key=lambda name: -(rates[name].higher_rate - rates[name].basic_rate),
        )
        inside_basic, above_basic = {}, {}
        band_left = remaining_basic_rate_band
        for name in basic_order:
            inside_basic[name], above_basic[name], band_left = _take(
                after_aea[name], band_left
            )

        # Gains above the basic rate band are split at the higher rate limit
        # so reforms can charge an additional rate; in law the two rates are
        # equal. Relief gains are the lowest part of the gains here too.
        higher_order = ["badr"] + sorted(
            rates,
            key=lambda name: -(rates[name].additional_rate - rates[name].higher_rate),
        )
        inside_higher, above_higher = {}, {}
        band_left = higher_rate_band
        for name in higher_order:
            inside_higher[name], above_higher[name], band_left = _take(
                above_basic[name], band_left
            )

        def schedule_tax(name):
            schedule = rates[name]
            return (
                inside_basic[name] * schedule.basic_rate
                + inside_higher[name] * schedule.higher_rate
                + above_higher[name] * schedule.additional_rate
            )

        # Relief gains are charged at their own flat rate whatever the band.
        main_tax = schedule_tax("main")
        badr_tax = after_aea["badr"] * cgt.badr.rate
        return (
            main_tax
            + badr_tax
            + schedule_tax("residential_property")
            + schedule_tax("carried_interest")
        )
