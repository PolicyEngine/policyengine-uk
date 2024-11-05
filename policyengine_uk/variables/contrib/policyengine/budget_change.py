from policyengine_uk.model_api import *


class pre_budget_change_household_benefits(Variable):
    value_type = float
    entity = Household
    label = "household benefits"
    documentation = "Total value of benefits received by household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "child_benefit",
        "esa_income",
        "housing_benefit",
        "income_support",
        "jsa_income",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "afcs",
        "bsp",
        "carers_allowance",
        "dla",
        "esa_contrib",
        "iidb",
        "incapacity_benefit",
        "jsa_contrib",
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "ssmg",
        "basic_income",
        "epg_subsidy",
        "cost_of_living_support_payment",
        "energy_bills_rebate",
    ]

    def formula(household, period, parameters):
        contrib = parameters(period).gov.contrib
        uprating = contrib.benefit_uprating
        benefits = pre_budget_change_household_benefits.adds
        if contrib.abolish_council_tax:
            benefits = [
                benefit
                for benefit in benefits
                if benefit != "council_tax_benefit"
            ]
        general_benefits = add(
            household,
            period,
            [
                benefit
                for benefit in benefits
                if benefit not in ["basic_income"]
            ],
        )
        non_sp_benefits = add(
            household,
            period,
            [
                benefit
                for benefit in benefits
                if benefit not in ["state_pension", "basic_income"]
            ],
        )
        return (
            add(household, period, benefits)
            + general_benefits * uprating.all
            + non_sp_benefits * uprating.non_sp
        )


class pre_budget_change_household_tax(Variable):
    value_type = float
    entity = Household
    label = "household taxes"
    documentation = "Total taxes owed by the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "expected_sdlt",
        "expected_ltt",
        "expected_lbtt",
        "corporate_sdlt",
        "business_rates",
        "council_tax",
        "domestic_rates",
        "fuel_duty",
        "tv_licence",
        "wealth_tax",
        "non_primary_residence_wealth_tax",
        "income_tax",
        "national_insurance",
        "LVT",
        "carbon_tax",
        "vat_change",
        "capital_gains_tax",
    ]

    def formula(household, period, parameters):
        if parameters(period).gov.contrib.abolish_council_tax:
            return add(
                household,
                period,
                [
                    tax
                    for tax in pre_budget_change_household_tax.adds
                    if tax not in ["council_tax"]
                ],
            )
        else:
            return add(household, period, pre_budget_change_household_tax.adds)


class pre_budget_change_household_net_income(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["household_market_income", "pre_budget_change_household_benefits"]
    subtracts = ["pre_budget_change_household_tax"]


class pre_budget_change_ons_household_income_decile(Variable):
    label = "pre-budget change household income decile (ONS matched)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        income = household("pre_budget_change_household_net_income", period)
        equivalisation = household("household_equivalisation_bhc", period)
        if household.simulation.dataset is not None:
            household_weight = household("household_weight", period)
            weighted_income = MicroSeries(
                income / equivalisation, weights=household_weight
            )
            decile = weighted_income.decile_rank().values
        else:
            upper_bounds = [
                16000.0,
                20700.0,
                24100.0,
                27200.0,
                31800.0,
                37200.0,
                45200.0,
                53300.0,
                68500.0,
                np.inf,
            ]

            equivalised_income = income / equivalisation
            decile = np.select(
                [equivalised_income <= upper_bounds[i] for i in range(10)],
                list(range(1, 11)),
            )
        # Set negatives to -1.
        # This avoids the bottom decile summing to a negative number,
        # which would flip the % change in the interface.
        return where(income < 0, -1, decile)


class nhs_budget_change(Variable):
    label = "NHS budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        budget_increase = (
            parameters(period).gov.contrib.policyengine.budget.nhs * 1e9
        )
        if budget_increase == 0:
            return 0
        decile = household(
            "pre_budget_change_ons_household_income_decile", period
        )
        weight = household("household_weight", period)
        DECILE_INCIDENCE = {
            1: 0.095,
            2: 0.118,
            3: 0.126,
            4: 0.117,
            5: 0.104,
            6: 0.104,
            7: 0.092,
            8: 0.089,
            9: 0.085,
            10: 0.07,
        }

        decile = pd.Series(decile)

        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if household.simulation.dataset is not None:
            households_per_decile = (
                pd.Series(weight).groupby(decile).sum().to_dict()
            )
        else:
            households_per_decile = {i: 28e5 for i in range(1, 11)}

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})


class education_budget_change(Variable):
    label = "education budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):

        budget_increase = (
            parameters(period).gov.contrib.policyengine.budget.education * 1e9
        )
        if budget_increase == 0:
            return 0
        decile = household(
            "pre_budget_change_ons_household_income_decile", period
        )
        weight = household("household_weight", period)
        DECILE_INCIDENCE = {
            1: 0.114,
            2: 0.146,
            3: 0.122,
            4: 0.125,
            5: 0.119,
            6: 0.085,
            7: 0.088,
            8: 0.076,
            9: 0.077,
            10: 0.046,
        }

        decile = pd.Series(decile)
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if household.simulation.dataset is not None:
            households_per_decile = (
                pd.Series(weight).groupby(decile).sum().to_dict()
            )
        else:
            households_per_decile = {i: 28e5 for i in range(1, 11)}

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})


class other_public_spending_budget_change(Variable):
    label = "non- budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):

        budget_increase = (
            parameters(
                period
            ).gov.contrib.policyengine.budget.other_public_spending
            * 1e9
        )
        if budget_increase == 0:
            return 0
        decile = household(
            "pre_budget_change_ons_household_income_decile", period
        )
        weight = household("household_weight", period)
        DECILE_INCIDENCE = {
            1: 0.114,
            2: 0.146,
            3: 0.122,
            4: 0.125,
            5: 0.119,
            6: 0.085,
            7: 0.088,
            8: 0.076,
            9: 0.077,
            10: 0.046,
        }

        decile = pd.Series(decile)
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if household.simulation.dataset is not None:
            households_per_decile = (
                pd.Series(weight).groupby(decile).sum().to_dict()
            )
        else:
            households_per_decile = {i: 28e5 for i in range(1, 11)}

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})


class corporate_incident_tax_revenue_change(Variable):
    label = "corporate-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        share = household("shareholding", period)
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.corporate_incident_tax_change
        return revenue_change * share * 1e9


class high_income_incident_tax_change(Variable):
    label = "high income-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        if household.simulation.dataset is None:
            return 0

        total_income = household.members("total_income", period)
        high_income = household.sum(max_(total_income - 100e3, 0))
        weight = household("household_weight", period)
        share = high_income / (high_income * weight).sum()
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.high_income_incident_tax_change
        return revenue_change * 1e9 * share


class consumer_incident_tax_revenue_change(Variable):
    label = "consumer-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        consumption = household("consumption", period)
        if (
            household.simulation.dataset is not None
            and household("consumption", period).sum() != 0
        ):
            weight = household("household_weight", period)
            share = consumption / (consumption * weight).sum()
        else:
            share = consumption / 846e9
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.consumer_incident_tax_change
        return revenue_change * share * 1e9
