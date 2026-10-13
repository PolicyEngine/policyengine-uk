import numpy as np
from policyengine_core.model_api import *

# Benefits whose simulated amount the reform replaces with the amount reported
# in the dataset year. Each needs a <name>_reported variable. Attendance
# Allowance, DLA and PIP are not listed: the data records their receipt as a
# rate category (aa_category, dla_m_category, dla_sc_category, pip_dl_category,
# pip_m_category), and the model pays that category's rate. The model has no
# reported amount for them to copy. The winter heating payments are set
# separately (see below).
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

# Tax credits are not paid below a minimum award, and each has a variable
# before that minimum, which takes the same reported amount.
PRE_MINIMUM = {
    "child_tax_credit": "child_tax_credit_pre_minimum",
    "working_tax_credit": "working_tax_credit_pre_minimum",
}

# Benefit-unit awards that cover only the claimant and partner, set from their
# own reports. The reported amounts of anyone else in the benefit unit (such
# as a non-dependent adult, who claims in their own right) stay in esa_income
# and jsa_income, which count in household income. They never enter the
# claimant's or partner's award.
CLAIMANT_OR_PARTNER_AWARDS = {
    "esa_income": "claimant_or_partner_esa_income",
    "jsa_income": "claimant_or_partner_jsa_income",
}

# Income Support is the claimant's family's award, so it is set from the
# claimant's and partner's reports only. That is all the model ever pays as
# income_support: with the reform off, would_claim_IS and
# income_support_eligible read only their reports too. Another member's own
# Income Support report (a non-dependent adult claiming in their own right) is
# in household income neither with the reform nor without it. ESA and JSA
# differ: esa_income and jsa_income count every member's award either way.
CLAIMANT_OR_PARTNER_ONLY = ["income_support"]

# The model's move off legacy benefits (legacy_benefits_closed): once a legacy
# benefit a family reports has closed, DWP's migration notice ends all its
# legacy awards, and it claims Universal Credit or goes to Pension Credit. The
# reform pays every listed benefit, the legacy ones and Universal Credit alike,
# at its dataset-year report in every year, so it moves no family. It holds
# these false for its years, so that everything that reads them (such as the
# legacy benefits' eligibility and the "on" statuses read from it, the
# Universal Credit claim, and Housing Benefit and tax credit eligibility)
# agrees with the awards it pays.
NOT_MOVED = ["legacy_benefits_closed"]

YEARS_IN_FUTURE = 10


def disable_simulated_benefits(parameters, period):
    if parameters(period).gov.contrib.policyengine.disable_simulated_benefits:

        class DisableSimulatedBenefits(Reform):
            """Use the dataset year's reported benefit amounts in every year.

            Each listed benefit is set, in the dataset year and the nine years
            after it, to its amount reported in the dataset year. The amount
            is not uprated, while most of the *_reported variables are.

            The claimant-or-partner awards are set the same way, from the
            dataset-year reports of whoever is the claimant or partner in
            each year (is_claimant_or_partner); Income Support is set from
            those reports alone. So every amount is the same in every year,
            except that these three change when who is the claimant or
            partner changes. Readers of those awards, including the
            Income Support gate, cannot tell an award set here from one
            entered directly. In a later year, esa_income and jsa_income match
            neither the award on that year's uprated reports nor their total.
            Without the claimant-or-partner awards set here, the readers would
            take the whole of esa_income or jsa_income, including another
            member's award, to be the claimant's or partner's.

            No family is moved off its legacy benefits (NOT_MOVED): the
            reform pays them as reported in every year, after the dates
            from which the model closes them included.

            As the amounts are inputs, a reform that changes a benefit's
            parameters does not change them. A reform that neutralizes a
            benefit removes it, and neutralizing esa_income or jsa_income
            also neutralizes its claimant-or-partner award
            (CountryTaxBenefitSystem.variable_parts). A neutralized variable
            ignores what the reform sets for it.
            """

            def apply(self):
                simulation = self.simulation
                system = simulation.tax_benefit_system
                time_period = int(str(simulation.dataset.time_period)[:4])
                years = range(time_period, time_period + YEARS_IN_FUTURE)

                def reported(variable, members=None):
                    """A benefit's reported amount in the dataset year, for
                    the given members, summed over the benefit's entity."""
                    amounts = simulation.calculate(variable + "_reported", time_period)
                    if members is not None:
                        amounts = amounts * members
                    entity = system.variables[variable].entity.key
                    population = simulation.populations[entity]
                    if population.entity.is_person:
                        return amounts
                    return population.sum(amounts)

                for year in years:
                    claimant_or_partner = simulation.calculate(
                        "is_claimant_or_partner", year
                    )
                    values = {}
                    for variable in BENEFITS:
                        members = (
                            claimant_or_partner
                            if variable in CLAIMANT_OR_PARTNER_ONLY
                            else None
                        )
                        values[variable] = reported(variable, members)
                        if variable in PRE_MINIMUM:
                            values[PRE_MINIMUM[variable]] = values[variable]
                        if variable in CLAIMANT_OR_PARTNER_AWARDS:
                            values[CLAIMANT_OR_PARTNER_AWARDS[variable]] = reported(
                                variable, claimant_or_partner
                            )
                    for variable in NOT_MOVED:
                        entity = system.variables[variable].entity.key
                        count = simulation.populations[entity].count
                        values[variable] = np.zeros(count, dtype=bool)
                    for target, value in values.items():
                        simulation.set_input(target, year, value)

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
