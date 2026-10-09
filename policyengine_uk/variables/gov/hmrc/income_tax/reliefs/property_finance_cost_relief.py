from policyengine_uk.model_api import *


class property_finance_cost_relief(Variable):
    value_type = float
    entity = Person
    label = "residential property finance costs tax reduction"
    documentation = (
        "Tax reduction for the costs of dwelling-related loans that cannot be "
        "deducted from property profits: the property basic rate (the basic "
        "rate before 2027-28) times the finance costs relieved this year. "
        "The rate is the same for Scottish taxpayers, whose property income "
        "is taxed at Scottish rates. It is deducted at Step 6 of the income "
        "tax calculation after the person's other tax reductions, and only "
        "so far as there is tax left to deduct it from."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 274A",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/274A",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 274AA(5)",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
        ),
        dict(
            title="Finance Act 2026, Sch. 1 para. 40 (property basic rate from 2027-28)",
            href="https://www.legislation.gov.uk/ukpga/2026/11/schedule/1",
        ),
        dict(
            title="Income Tax Act 2007, s. 26(1)(a) and s. 29(2)-(3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
    ]

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        reduction = income_tax.rates.property.basic * person(
            "property_finance_costs_relieved", period
        )
        # The order of Step 6 reductions does not change their total, so the
        # person's other reductions come first; this one is limited to the
        # Step 5 tax they leave. Step 7 charges (ITA 2007 s. 30), such as the
        # High Income Child Benefit Charge, are not reduced.
        other_reductions = [
            variable
            for variable in income_tax.income_tax_subtractions
            if variable != "property_finance_cost_relief"
        ]
        tax_left = max_(
            0,
            person("income_tax_pre_charges", period)
            - add(person, period, other_reductions),
        )
        return min_(reduction, tax_left)
