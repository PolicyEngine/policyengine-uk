from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import (
    calc_income_tax_with_gift_aid,
    first_extended_scottish_threshold,
)


class property_income_tax(Variable):
    documentation = (
        "Property income uses the UK main scale before 2017-18. From "
        "2017-18, Scottish taxpayers use the Scottish main scale. Other "
        "UK taxpayers use the UK main scale until separate property rates "
        "apply from 2027-28. Property income is stacked after other "
        "non-savings income."
    )

    value_type = float
    entity = Person
    label = "Income tax on property income"
    definition_period = YEAR
    reference = (
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 268",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/268",
        ),
        dict(
            title="OBR Economic and Fiscal Outlook November 2025",
            href="https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/",
        ),
        dict(
            title="Finance Act 2026, s. 6 (commencement in 2027-28)",
            href="https://www.legislation.gov.uk/ukpga/2026/11/section/6/enacted",
        ),
        dict(
            title="Finance Act 2026, s. 7 (property income rates)",
            href="https://www.legislation.gov.uk/ukpga/2026/11/section/7/enacted",
        ),
        dict(
            title="Budget 2026, paragraph 6.246 (property rates of 24%, 44% and 49%)",
            href="https://assets.publishing.service.gov.uk/media/6ae1ec57bdb574cf1c9b3f12/E03668986_HMT_Budget_2026_ELAY__2_.pdf#page=142",
        ),
        dict(
            title="Income Tax Act 2007, s. 11A as at 6 April 2016",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/11A/2016-04-06",
        ),
        dict(
            title=(
                "The Scotland Act 2012, Section 25 (Appointed Years) Order 2015, art. 3"
            ),
            href="https://www.legislation.gov.uk/uksi/2015/2000/article/3/made",
        ),
        dict(
            title="Scottish Rate of Income Tax Resolution 2016-17 (S4M-15497)",
            href="https://www.parliament.scot/chamber-and-committees/official-report/"
            "search-what-was-said-in-parliament/meeting-of-parliament-11-02-2016"
            "?iob=95367&meeting=10365",
        ),
    )
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        property_after_allowances = person(
            "taxable_property_income_after_allowances", period
        )
        other_earned_taxable = max_(
            0,
            person("non_savings_income_after_allowances", period)
            - property_after_allowances,
        )
        gross_gift = person("gift_aid_grossed_up", period)
        return calc_income_tax_with_gift_aid(
            rates.uk,
            other_earned_taxable + property_after_allowances,
            gross_gift,
        ) - calc_income_tax_with_gift_aid(rates.uk, other_earned_taxable, gross_gift)

    def formula_2017(person, period, parameters):
        """Before 2027-28, property income uses the applicable main scale."""
        rates = parameters(period).gov.hmrc.income_tax.rates
        property_after_allowances = person(
            "taxable_property_income_after_allowances", period
        )
        other_earned_taxable = max_(
            0,
            person("non_savings_income_after_allowances", period)
            - property_after_allowances,
        )
        gross_gift = person("gift_aid_grossed_up", period)
        ruk_tax = calc_income_tax_with_gift_aid(
            rates.uk,
            other_earned_taxable + property_after_allowances,
            gross_gift,
        ) - calc_income_tax_with_gift_aid(rates.uk, other_earned_taxable, gross_gift)
        first_extended = first_extended_scottish_threshold(rates.scotland.rates)
        scottish_tax = calc_income_tax_with_gift_aid(
            rates.scotland.rates,
            other_earned_taxable + property_after_allowances,
            gross_gift,
            first_extended,
            len(rates.scotland.rates.thresholds),
        ) - calc_income_tax_with_gift_aid(
            rates.scotland.rates,
            other_earned_taxable,
            gross_gift,
            first_extended,
            len(rates.scotland.rates.thresholds),
        )
        return where(person("pays_scottish_income_tax", period), scottish_tax, ruk_tax)

    def formula_2027(person, period, parameters):
        """
        Calculate income tax on property income.

        For Scottish taxpayers, property income is taxed using the normal
        Scottish income tax rates (the new property-specific rates do not
        apply to Scotland).

        For rUK taxpayers, property income is taxed using property-specific
        rates. From April 2027, these are 4pp higher than standard UK rates
        (24%, 44%, 49% vs 20%, 40%, 45%): 2pp from Budget 2025 and a further
        2pp from Budget 2026 (paragraph 6.246), which applies them across
        England, Wales and Northern Ireland.

        Property income is stacked on top of other earned income for
        determining which tax band it falls into.
        """
        rates = parameters(period).gov.hmrc.income_tax.rates
        non_savings_after_allowances = person(
            "non_savings_income_after_allowances", period
        )
        property_after_allowances = person(
            "taxable_property_income_after_allowances", period
        )
        other_earned_taxable = max_(
            0, non_savings_after_allowances - property_after_allowances
        )
        is_scottish = person("pays_scottish_income_tax", period)

        # Scottish taxpayers: use Scottish rates via calc method
        # Tax on (other earned + property) minus tax on (other earned)
        gross_gift = person("gift_aid_grossed_up", period)
        first_extended = first_extended_scottish_threshold(rates.scotland.rates)
        scottish_tax = calc_income_tax_with_gift_aid(
            rates.scotland.rates,
            other_earned_taxable + property_after_allowances,
            gross_gift,
            first_extended,
            len(rates.scotland.rates.thresholds),
        ) - calc_income_tax_with_gift_aid(
            rates.scotland.rates,
            other_earned_taxable,
            gross_gift,
            first_extended,
            len(rates.scotland.rates.thresholds),
        )

        # rUK taxpayers: use property-specific rates
        property_rates = rates.property
        thresholds = rates.uk.thresholds
        basic_upper = thresholds[1] + gross_gift
        higher_upper = thresholds[2] + gross_gift

        # Property income in basic rate band
        basic_rate_space = max_(0, basic_upper - other_earned_taxable)
        property_in_basic = min_(property_after_allowances, basic_rate_space)

        # Property income in higher rate band
        higher_start = max_(other_earned_taxable, basic_upper)
        higher_rate_space = max_(0, higher_upper - higher_start)
        remaining_after_basic = max_(0, property_after_allowances - property_in_basic)
        property_in_higher = min_(remaining_after_basic, higher_rate_space)

        # Property income in additional rate band
        property_in_additional = max_(
            0, property_after_allowances - property_in_basic - property_in_higher
        )

        ruk_tax = (
            property_rates.basic * property_in_basic
            + property_rates.higher * property_in_higher
            + property_rates.additional * property_in_additional
        )

        return where(is_scottish, scottish_tax, ruk_tax)
