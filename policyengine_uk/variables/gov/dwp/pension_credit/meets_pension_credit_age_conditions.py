from policyengine_uk.model_api import *


class meets_pension_credit_age_conditions(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets the State Pension Credit age conditions"
    documentation = (
        "The claimant has reached the qualifying age for State Pension Credit "
        "and, while the mixed-age couple exclusion is in force (from 15 May "
        "2019), so has any partner, unless the couple keeps Pension Credit "
        "under the SI 2019/37 article 4 saving. A family meeting these "
        "conditions is on the pension-age route (Pension Credit and pension-age "
        "Housing Benefit) and is not eligible for Universal Credit."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        count = benunit.sum(claimant_or_partner)
        all_pension_age = (count > 0) & (
            benunit.sum(claimant_or_partner & person("is_SP_age", period)) == count
        )
        # Parameters are read at 30 April of the model year
        # (convert_to_fiscal_year_parameters), so model year 2019 (2019-20)
        # falls before the 15 May 2019 exclusion. Couples already on Pension
        # Credit or pension-age Housing Benefit on 14 May 2019 kept them, so
        # the old rule is the closer approximation for that year.
        excluded = parameters(period).gov.dwp.pension_credit.mixed_age_couples.excluded
        saving = benunit("has_mixed_age_couple_pension_credit_saving", period)
        # Before the exclusion a mixed-age couple could claim either Pension
        # Credit or Universal Credit jointly (UC Regs 2013 reg 3(2)(a)); a
        # couple reported on Universal Credit stays on it, and any other takes
        # the Pension Credit route. This is a modelling choice.
        reports_uc = add(benunit, period, ["universal_credit_reported"]) > 0
        before_exclusion = np.logical_not(excluded) & ~reports_uc
        mixed_age_route = benunit("is_mixed_age_couple", period) & (
            before_exclusion | saving
        )
        return all_pension_age | mixed_age_route
