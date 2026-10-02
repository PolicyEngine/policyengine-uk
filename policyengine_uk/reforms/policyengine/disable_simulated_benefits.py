from policyengine_core.model_api import *

# Benefits whose simulated amount the reform replaces with the amount reported
# in the dataset year. Each needs a <name>_reported variable. Attendance
# Allowance, DLA and PIP are not listed: the data records their receipt as a
# rate category (aa_category, dla_m_category, dla_sc_category, pip_dl_category,
# pip_m_category), and the model pays that category's rate. The model has no
# reported amount for them to copy.
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
    "winter_fuel_allowance",
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

# Income Support is the claimant's family's award (income_support_eligible
# needs the claimant's or partner's own report), so it is set from the
# claimant's and partner's reports only.
CLAIMANT_OR_PARTNER_ONLY = ["income_support"]

YEARS_IN_FUTURE = 10


def disable_simulated_benefits(parameters, period):
    if parameters(period).gov.contrib.policyengine.disable_simulated_benefits:

        class DisableSimulatedBenefits(Reform):
            """Use the dataset year's reported benefit amounts in every year.

            Each listed benefit is set, in the dataset year and the nine years
            after it, to its amount reported in the dataset year. The amount
            is the same in every year: it is not uprated, unlike the
            *_reported variables, which are.

            The claimant-or-partner awards are set the same way, from the
            claimant's and partner's own reports in the dataset year
            (is_claimant_or_partner). Readers of those awards, including the
            Income Support gate, cannot tell an award set here from one
            entered directly. In a later year, esa_income and jsa_income match
            neither the award on that year's uprated reports nor their total.
            Without the claimant-or-partner awards set here, the readers would
            take the whole of esa_income or jsa_income, including another
            member's award, to be the claimant's or partner's.
            """

            def apply(self):
                simulation = self.simulation
                system = simulation.tax_benefit_system
                time_period = int(str(simulation.dataset.time_period)[:4])
                years = range(time_period, time_period + YEARS_IN_FUTURE)
                claimant_or_partner = simulation.calculate(
                    "is_claimant_or_partner", time_period
                )

                def reported(variable, entity, members=None):
                    """A benefit's reported amount in the dataset year,
                    summed over the given members of each entity."""
                    amounts = simulation.calculate(variable + "_reported", time_period)
                    if members is not None:
                        amounts = amounts * members
                    population = simulation.populations[entity]
                    if population.entity.is_person:
                        return amounts
                    return population.sum(amounts)

                for variable in BENEFITS:
                    entity = system.variables[variable].entity.key
                    members = (
                        claimant_or_partner
                        if variable in CLAIMANT_OR_PARTNER_ONLY
                        else None
                    )
                    values = {variable: reported(variable, entity, members)}
                    if variable in PRE_MINIMUM:
                        values[PRE_MINIMUM[variable]] = values[variable]
                    if variable in CLAIMANT_OR_PARTNER_AWARDS:
                        values[CLAIMANT_OR_PARTNER_AWARDS[variable]] = reported(
                            variable, entity, claimant_or_partner
                        )
                    for year in years:
                        for target, value in values.items():
                            simulation.set_input(target, year, value)

        return DisableSimulatedBenefits
