from policyengine_uk.model_api import *


class property_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on property income"
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 268",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/268",
        ),
        dict(
            title="OBR Economic and Fiscal Outlook November 2025",
            href="https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        """
        Calculate income tax on property income.

        For Scottish taxpayers, property income is taxed using the normal
        Scottish income tax rates (the new property-specific rates do not
        apply to Scotland).

        For rUK taxpayers, property income is taxed using property-specific
        rates. From April 2027, these are 2pp higher than standard UK rates
        (22%, 42%, 47% vs 20%, 40%, 45%).

        Property income is stacked on top of other earned income for
        determining which tax band it falls into.
        """
        rates = parameters(period).gov.hmrc.income_tax.rates
        taxable_property = person("taxable_property_income", period)
        earned_taxable = person("earned_taxable_income", period)
        other_earned_taxable = max_(0, earned_taxable - taxable_property)
        is_scottish = person("pays_scottish_income_tax", period)

        # Scottish taxpayers: use Scottish rates via calc method
        # Tax on (other earned + property) minus tax on (other earned)
        scottish_tax = rates.scotland.rates.calc(
            other_earned_taxable + taxable_property
        ) - rates.scotland.rates.calc(other_earned_taxable)

        # rUK taxpayers: use property-specific rates
        property_rates = rates.property
        thresholds = rates.uk.thresholds
        basic_upper = thresholds[1]  # Higher rate threshold
        higher_upper = thresholds[2]  # Additional rate threshold

        # Property income in basic rate band
        basic_rate_space = max_(0, basic_upper - other_earned_taxable)
        property_in_basic = min_(taxable_property, basic_rate_space)

        # Property income in higher rate band
        higher_start = max_(other_earned_taxable, basic_upper)
        higher_rate_space = max_(0, higher_upper - higher_start)
        remaining_after_basic = max_(0, taxable_property - property_in_basic)
        property_in_higher = min_(remaining_after_basic, higher_rate_space)

        # Property income in additional rate band
        property_in_additional = max_(
            0, taxable_property - property_in_basic - property_in_higher
        )

        ruk_tax = (
            property_rates.basic * property_in_basic
            + property_rates.higher * property_in_higher
            + property_rates.additional * property_in_additional
        )

        return where(is_scottish, scottish_tax, ruk_tax)
