from policyengine_core.model_api import *

# Benefits set to the amount the survey reports, <benefit>_reported, in place
# of the simulated amount. Attendance Allowance, DLA and PIP are not listed:
# they are paid at the rate of the award category the survey reports
# (aa_category, dla_sc_category, dla_m_category, pip_dl_category and
# pip_m_category), so they already follow the reported award. The winter
# heating payments are set separately (see below).
BENEFITS = [
    "afcs",
    "bsp",
    "carers_allowance",
    "child_benefit",
    "child_tax_credit",
    "council_tax_benefit",
    "esa_contrib",
    "esa_income",
    "housing_benefit",
    "iidb",
    "incapacity_benefit",
    "income_support",
    "jsa_contrib",
    "jsa_income",
    "pension_credit",
    "sda",
    "ssmg",
    "state_pension",
    "universal_credit",
    "working_tax_credit",
]

YEARS_IN_FUTURE = 10


def disable_simulated_benefits(parameters, period):
    if parameters(period).gov.contrib.policyengine.disable_simulated_benefits:

        class DisableSimulatedBenefits(Reform):
            def apply(self):
                simulation = self.simulation
                time_period = int(simulation.dataset.time_period)
                years = range(time_period, time_period + YEARS_IN_FUTURE)

                for variable in BENEFITS:
                    entity = simulation.tax_benefit_system.variables[
                        variable
                    ].entity.key
                    reported_value = simulation.calculate(
                        variable + "_reported", time_period, map_to=entity
                    )
                    for year in years:
                        simulation.set_input(variable, year, reported_value)

                    if variable in ["child_tax_credit", "working_tax_credit"]:
                        # CTC and WTC have their own pre_minimum variables because tax credits aren't paid if
                        # below a threshold.
                        variable = variable + "_pre_minimum"
                        for year in years:
                            simulation.set_input(variable, year, reported_value)

                # The survey reports one winter heating payment: FRS benefit
                # code 62, which policyengine-uk-data loads into
                # winter_fuel_allowance_reported for every respondent,
                # Scotland included. Scotland's payment has been the Pension
                # Age Winter Heating Payment since the 2024 qualifying week,
                # so in each year a Scottish household's report becomes its
                # pawhp while PAWHP is paid, and its winter_fuel_allowance
                # before then. Both variables are household income, so each
                # report is counted once, under the scheme that pays it.
                reported_winter_heating = np.asarray(
                    simulation.calculate(
                        "winter_fuel_allowance_reported",
                        time_period,
                        map_to="household",
                    )
                )
                in_scotland = (
                    np.asarray(simulation.calculate("country", time_period))
                    == "SCOTLAND"
                )
                for year in years:
                    paid_as_pawhp = (
                        in_scotland
                        & parameters(year).gov.social_security_scotland.pawhp.active
                    )
                    simulation.set_input(
                        "winter_fuel_allowance",
                        year,
                        np.where(paid_as_pawhp, 0, reported_winter_heating),
                    )
                    simulation.set_input(
                        "pawhp",
                        year,
                        np.where(paid_as_pawhp, reported_winter_heating, 0),
                    )

        return DisableSimulatedBenefits
