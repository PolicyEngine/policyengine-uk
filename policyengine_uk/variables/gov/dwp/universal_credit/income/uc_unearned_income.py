from policyengine_uk.model_api import *


class uc_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    documentation = (
        "Income falling within the descriptions in regulation 66(1) of the "
        "Universal Credit Regulations 2013. Capital counts only through its "
        "assumed yield (uc_tariff_income, regulation 72(1)); actual interest, "
        "dividends and rent are not unearned income at any capital level."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/66"

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (UC Regs 2013 reg 22); dropping dependants'
        # own income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        p = parameters(period).gov.dwp.universal_credit.means_test
        return add_for_members(benunit, period, p.income_definitions.unearned, members)
