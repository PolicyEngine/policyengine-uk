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
        Calculate income tax on property income using property-specific rates.

        Property income is stacked on top of other earned income (employment,
        pension, self-employment) for determining which tax band it falls into.
        From April 2027, property income is taxed at rates 2pp higher than
        standard UK rates (22%, 42%, 47% vs 20%, 40%, 45%).
        """
        property_rates = parameters(period).gov.hmrc.income_tax.rates.property
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        personal_allowance = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_allowance.amount

        # Get taxable property income (after property allowance)
        taxable_property = person("taxable_property_income", period)

        # Get other earned income that comes before property in the stack
        # Property income sits within earned_taxable_income, which includes:
        # - employment income
        # - pension income
        # - self-employment income
        # - property income
        # We need the portion excluding property to know where property starts
        earned_taxable = person("earned_taxable_income", period)
        other_earned_taxable = max_(0, earned_taxable - taxable_property)

        # Calculate how much property income falls in each band
        # Band boundaries (after personal allowance is accounted for in
        # earned_taxable_income calculation)
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

        # Apply property-specific rates
        return (
            property_rates.basic * property_in_basic
            + property_rates.higher * property_in_higher
            + property_rates.additional * property_in_additional
        )
