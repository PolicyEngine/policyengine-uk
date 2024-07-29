In time period t:

household_income = labour_income + non_labour_income - taxes + benefits
household_consumption = non_mortgage_interest_consumption + mortgage_interest
household_savings = income - consumption
other_savings = savings - mortgage_capital_repayment
household_wealth = property_wealth + corporate_wealth + financial_wealth
gov_income = taxes
gov_spending = benefits + public_services

In time period t+1:

financial_wealth = financial_wealth(t) + mortgage_capital_repayment(t) + other_savings(t)

labour_income = labour_income(t) * obr_labour_income_uprating
non_labour_income = labour_income(t) * obr_non_labour_income_uprating
non_mortgage_interest_consumption = non_mortgage_interest_consumption(t) * obr_cpi_uprating
mortgage_interest = mortgage_interest(t) * obr_average_mortgage_interest_rate_uprating



