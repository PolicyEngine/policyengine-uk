from policyengine_uk.model_api import *


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
        "(s. 227(4A)-(4B)). A Scottish taxpayer pays the Scottish rates, with "
        "the Scottish basic rate on any slice within the Scottish basic rate "
        "limit (s. 227(4AA)). Contributions above the annual allowance still "
        "get relief (pension_contributions_relief), so the charge recovers that "
        "relief once rather than taxing the excess twice."
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
        # Reduced net income is income after allowances (ITA 2007 s. 23
        # Step 3). Pension contributions relief and Gift Aid are deductions
        # here, where the law instead extends the rate limits (s. 227(4C)),
        # which places the chargeable amount at the same point in the bands.
        reduced_net_income = max_(
            0,
            person("adjusted_net_income", period) - person("allowances", period),
        )
        top_of_charge = reduced_net_income + chargeable_amount

        uk_charge = rates.uk.calc(top_of_charge) - rates.uk.calc(reduced_net_income)

        scottish_rates = rates.scotland.rates
        scottish_charge = scottish_rates.calc(top_of_charge) - scottish_rates.calc(
            reduced_net_income
        )
        # s. 227(4AA)(b)(i): no slice is charged at the starter rate. The
        # Scottish basic rate applies to every slice up to the Scottish basic
        # rate limit, so lift the starter band to the basic rate. The starter
        # bracket is null before 2018-19, when the lowest Scottish rate was the
        # basic rate.
        starter_bracket = person.simulation.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.scotland.rates.brackets[
            0
        ]
        if starter_bracket.rate(period.start) is not None:
            starter_rate = scottish_rates.rates[0]
            scottish_basic_rate = scottish_rates.rates[1]
            starter_limit = scottish_rates.thresholds[1]
            starter_band_slice = min_(top_of_charge, starter_limit) - min_(
                reduced_net_income, starter_limit
            )
            scottish_charge += (scottish_basic_rate - starter_rate) * starter_band_slice

        return where(
            person("pays_scottish_income_tax", period),
            scottish_charge,
            uk_charge,
        )
