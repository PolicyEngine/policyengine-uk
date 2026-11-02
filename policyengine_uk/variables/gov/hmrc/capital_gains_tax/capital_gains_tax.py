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


# Each pass of the exemption allocation ends where a schedule's gains cross a
# band boundary, so a handful is enough; four schedules in three bands give at
# most twelve boundaries.
_MAX_EXEMPTION_PASSES = 16


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
        "against the gains where it saves most tax, pound by pound "
        "(TCGA 1992 s. 1K(5)); the unused basic rate band goes to relief gains first, as "
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
        # beneficial to the taxpayer. Each pound saves the tax it would have
        # borne at the margin, which depends on the schedule it comes off and,
        # where removing it frees band for another schedule, on that schedule
        # too. So the exemption is set greedily: in each pass, against the
        # schedule where a pound saves most, up to the point where any
        # schedule's gains cross a band boundary and the saving can change.
        # Ties keep declaration order. Under current law, where the higher and
        # additional rates are equal, this gives the same allocation as
        # ranking the schedules by rate, apart from float rounding where the
        # exemption is split across schedules.
        names = list(amounts)
        flat_rate = {"badr": cgt.badr.rate}

        def slices(schedule_amounts):
            inside_basic, inside_higher, above_higher = allocate_bands(schedule_amounts)
            result = []
            for name in names:
                if name in flat_rate:
                    band_rates = [flat_rate[name]] * 3
                else:
                    band_rates = [
                        rates[name].basic_rate,
                        rates[name].higher_rate,
                        rates[name].additional_rate,
                    ]
                parts = [inside_basic[name], inside_higher[name], above_higher[name]]
                result += list(zip(parts, band_rates))
            return result

        left = {name: amounts[name].astype(float) for name in names}
        used = {name: np.zeros_like(left[name]) for name in names}
        aea_left = np.full_like(left["main"], aea)
        step = 1e-6
        for _ in range(_MAX_EXEMPTION_PASSES):
            if not np.any(aea_left > 0):
                break
            base = slices(left)
            savings, room = [], []
            for name in names:
                nudged = dict(left)
                nudged[name] = left[name] - step
                saving = np.zeros_like(aea_left)
                distance = np.full_like(aea_left, np.inf)
                for (part, rate), (moved, _) in zip(base, slices(nudged)):
                    slope = np.round((moved - part) / step)
                    saving = saving - slope * rate
                    shrinking = (slope < 0) & (part > 0)
                    distance = where(
                        shrinking,
                        min_(distance, part / where(shrinking, -slope, 1)),
                        distance,
                    )
                active = (left[name] > 0) & (aea_left > 0)
                savings.append(where(active, np.round(saving, 9), -np.inf))
                room.append(min_(left[name], distance))
            savings = np.stack(savings)
            best = np.argmax(savings, axis=0)
            can_take = np.max(savings, axis=0) > -np.inf
            for i, name in enumerate(names):
                taken = where(can_take & (best == i), min_(aea_left, room[i]), 0)
                left[name] = left[name] - taken
                used[name] = used[name] + taken
                aea_left = aea_left - taken
        # Any exemption left after the passes, which only happens when gains
        # cross more band boundaries than there are passes, goes in
        # declaration order.
        for name in names:
            taken = min_(aea_left, left[name])
            used[name] = used[name] + taken
            aea_left = aea_left - taken
        # Where the whole exemption went against one schedule, deduct it in a
        # single step so that the passes add no rounding of their own.
        schedules_used = sum((used[name] > 0).astype(int) for name in names)
        after_aea = {
            name: where(
                schedules_used <= 1,
                where(
                    used[name] > 0,
                    amounts[name] - min_(amounts[name], aea),
                    amounts[name],
                ),
                amounts[name] - used[name],
            ).astype(amounts[name].dtype)
            for name in names
        }

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
