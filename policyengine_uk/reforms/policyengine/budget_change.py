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
        "ESA_income",
        "housing_benefit",
        "income_support",
        "JSA_income",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "AFCS",
        "BSP",
        "carers_allowance",
        "dla",
        "ESA_contrib",
        "IIDB",
        "incapacity_benefit",
        "JSA_contrib",
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "SSP",
        "SMP",
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
        "change_in_expected_sdlt",
        "change_in_expected_ltt",
        "change_in_expected_lbtt",
        "corporate_sdlt_change_incidence",
        "business_rates_change_incidence",
        "council_tax",
        "domestic_rates",
        "change_in_fuel_duty",
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
        if hasattr(household.simulation, "dataset"):
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
            print(decile)
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

        budget_increase = (
            parameters(period).gov.contrib.policyengine.budget.nhs * 1e9
        )
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if hasattr(household.simulation, "dataset"):
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

        budget_increase = (
            parameters(period).gov.contrib.policyengine.budget.education * 1e9
        )
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if hasattr(household.simulation, "dataset"):
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

        budget_increase = (
            parameters(
                period
            ).gov.contrib.policyengine.budget.other_public_spending
            * 1e9
        )
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if hasattr(household.simulation, "dataset"):
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


class household_tax(Variable):
    value_type = float
    entity = Household
    label = "household taxes"
    documentation = "Total taxes owed by the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "change_in_expected_sdlt",
        "change_in_expected_ltt",
        "change_in_expected_lbtt",
        "corporate_sdlt_change_incidence",
        "business_rates_change_incidence",
        "council_tax",
        "domestic_rates",
        "change_in_fuel_duty",
        "tv_licence",
        "wealth_tax",
        "non_primary_residence_wealth_tax",
        "income_tax",
        "national_insurance",
        "LVT",
        "carbon_tax",
        "vat_change",
        "capital_gains_tax",
        "corporate_incident_tax_revenue_change",
        "consumer_incident_tax_revenue_change",
    ]

    def formula(household, period, parameters):
        if parameters(period).gov.contrib.abolish_council_tax:
            return add(
                household,
                period,
                [
                    tax
                    for tax in household_tax.adds
                    if tax not in ["council_tax"]
                ],
            )
        else:
            return add(household, period, household_tax.adds)


class household_benefits(Variable):
    value_type = float
    entity = Household
    label = "household benefits"
    documentation = "Total value of benefits received by household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "child_benefit",
        "ESA_income",
        "housing_benefit",
        "income_support",
        "JSA_income",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "AFCS",
        "BSP",
        "carers_allowance",
        "dla",
        "ESA_contrib",
        "IIDB",
        "incapacity_benefit",
        "JSA_contrib",
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "SSP",
        "SMP",
        "ssmg",
        "basic_income",
        "epg_subsidy",
        "cost_of_living_support_payment",
        "energy_bills_rebate",
        "nhs_budget_change",
        "education_budget_change",
        "other_public_spending_budget_change",
    ]

    def formula(household, period, parameters):
        contrib = parameters(period).gov.contrib
        uprating = contrib.benefit_uprating
        benefits = household_benefits.adds
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


class consumer_incident_tax_revenue_change(Variable):
    label = "consumer-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        consumption = household("consumption", period)
        if (
            hasattr(household.simulation, "dataset")
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


class budget_change_reform(Reform):
    def apply(self):
        self.add_variables(
            pre_budget_change_ons_household_income_decile,
            pre_budget_change_household_benefits,
            pre_budget_change_household_tax,
            pre_budget_change_household_net_income,
            nhs_budget_change,
            education_budget_change,
            other_public_spending_budget_change,
            corporate_incident_tax_revenue_change,
            consumer_incident_tax_revenue_change,
        )
        self.update_variable(household_benefits)
        self.update_variable(household_tax)


def create_budget_change_reform(parameters, _):
    budget = parameters.gov.contrib.policyengine.budget
    for child in budget.children:
        for iteration in budget.children[child].values_list:
            if iteration.value != 0:
                return budget_change_reform

    return None
