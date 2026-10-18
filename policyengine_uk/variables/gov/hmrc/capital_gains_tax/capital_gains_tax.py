import numpy as np

from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_gains import badr_gains_before_response


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
        "of capital_gains before any realisation response: relief gains move by "
        "their own response (capital_gains_badr_behavioural_response) and the "
        "other two in proportion with the rest of the gains. All three are "
        "clipped so that together they never exceed capital_gains. The annual "
        "exempt amount is set "
        "against the schedule whose top gains are charged at the highest rate "
        "first (TCGA 1992 s. 1K(5)); the unused basic rate band goes to relief gains first, as "
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
            person("allowances", period) - personal_pension_band_extension,
        )
        taxable_income = max_(
            0,
            person("net_income", period) - allowances_for_cgt_income,
        )
        capital_gains = person("capital_gains", period)
        gains = max_(0, capital_gains)
        aea = cgt.annual_exempt_amount
        basic_rate_limit = it.rates.uk.thresholds[1] + basic_rate_band_extension
        remaining_basic_rate_band = max_(basic_rate_limit - taxable_income, 0)
        higher_rate_limit = it.rates.uk.thresholds[2] + basic_rate_band_extension
        # Gains are the top slice of income (TCGA 1992 s. 1H), so the gains
        # above the basic rate band start at the basic rate limit or at
        # taxable income, whichever is higher. Only the rest of the band up to
        # the higher rate limit is left for them.
        remaining_higher_rate_band = max_(
            higher_rate_limit - max_(taxable_income, basic_rate_limit), 0
        )

        # The schedule inputs describe gains before any realisation response.
        # Relief gains move by their own response, which has its own
        # elasticity; the other schedules move in proportion with the rest of
        # the gains. Anything else that moves capital_gains away from the gains
        # after response, such as a marginal pound added to measure a marginal
        # rate, is shared across all the schedules in proportion. Then clip
        # each against what is left of the realised gains so inconsistent
        # inputs cannot exceed the total; the remainder is charged at the main
        # rates.
        before_response = person("capital_gains_before_response", period)
        response = person("capital_gains_behavioural_response", period)
        badr_response = person("capital_gains_badr_behavioural_response", period)
        after_response = before_response + response
        has_after_response = after_response > 0
        ratio = where(
            has_after_response,
            capital_gains / where(has_after_response, after_response, 1),
            1,
        )
        other_gains = before_response - badr_gains_before_response(person, period)
        has_other_gains = other_gains > 0
        other_scale = where(
            has_other_gains,
            (other_gains + response - badr_response)
            / where(has_other_gains, other_gains, 1),
            1,
        )

        def component(amount):
            return max_(0, amount * ratio)

        badr = min_(
            min_(
                component(person("capital_gains_badr", period) + badr_response),
                cgt.badr.lifetime_limit,
            ),
            gains,
        )
        residential = min_(
            component(
                person("capital_gains_residential_property", period) * other_scale
            ),
            gains - badr,
        )
        carried = min_(
            component(person("capital_gains_carried_interest", period) * other_scale),
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
        # Basic rate band. Relief gains take it first, TCGA 1992 s. 1I(4)-(6).
        # The taxpayer then allocates the rest, s. 1I(7)-(9), which saves most
        # on the schedule with the widest higher-minus-basic gap. Carried
        # interest from 2025-26 has no gap and comes last, matching its
        # exclusion from the band by Finance Act 2025 s. 12.
        basic_order = ["badr"] + sorted(
            rates,
            key=lambda name: -(rates[name].higher_rate - rates[name].basic_rate),
        )
        # Gains above the basic rate band are split at the higher rate limit,
        # stacked on top of taxable income, so reforms can charge an
        # additional rate; in law the two rates are equal. Relief gains are
        # the lowest part of the gains here too.
        higher_order = ["badr"] + sorted(
            rates,
            key=lambda name: -(rates[name].additional_rate - rates[name].higher_rate),
        )

        def allocate_bands(schedule_amounts):
            inside_basic, above_basic = {}, {}
            band_left = remaining_basic_rate_band
            for name in basic_order:
                inside_basic[name], above_basic[name], band_left = _take(
                    schedule_amounts[name], band_left
                )
            inside_higher, above_higher = {}, {}
            band_left = remaining_higher_rate_band
            for name in higher_order:
                inside_higher[name], above_higher[name], band_left = _take(
                    above_basic[name], band_left
                )
            return inside_basic, inside_higher, above_higher

        # Annual exempt amount, TCGA 1992 s. 1K(5): deducted in the way most
        # beneficial to the taxpayer, which is against the schedule whose top
        # gains are charged at the highest rate first. A schedule's top gains
        # are at its additional rate when, before the exemption, any of them
        # reach above the higher rate band, which happens whenever taxable
        # income is already above the higher rate limit; otherwise they are
        # at its higher rate. Relief gains carry their own flat rate. The
        # order is set for each person, and ties keep declaration order.
        _, _, above_higher_before_aea = allocate_bands(amounts)
        names = list(amounts)
        top_rate = np.stack(
            [
                (
                    np.full_like(amounts[name], cgt.badr.rate, dtype=float)
                    if name == "badr"
                    else where(
                        above_higher_before_aea[name] > 0,
                        rates[name].additional_rate,
                        rates[name].higher_rate,
                    )
                )
                for name in names
            ]
        )
        stacked = np.stack([amounts[name] for name in names])
        order = np.argsort(-top_rate, axis=0, kind="stable")
        stacked_after_aea = np.empty_like(stacked)
        aea_left = aea
        for position in range(len(names)):
            index = order[position : position + 1]
            amount = np.take_along_axis(stacked, index, axis=0)[0]
            used = min_(amount, aea_left)
            np.put_along_axis(stacked_after_aea, index, (amount - used)[None], axis=0)
            aea_left = aea_left - used
        after_aea = {name: stacked_after_aea[i] for i, name in enumerate(names)}

        inside_basic, inside_higher, above_higher = allocate_bands(after_aea)

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
