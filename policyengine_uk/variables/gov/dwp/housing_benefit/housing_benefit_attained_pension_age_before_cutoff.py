from policyengine_uk.model_api import *


class housing_benefit_attained_pension_age_before_cutoff(Variable):
    value_type = bool
    entity = BenUnit
    label = "a member attained State Pension age before the Housing Benefit cutoff"
    documentation = (
        "Whether any member of the benefit unit attained State Pension age "
        "before the pension-age cutoff (1 April 2021). Such units keep the "
        "higher pension-age personal allowance; units whose members all "
        "attained it on or after the cutoff get the lower one. Before the "
        "cutoff took effect there was a single pension-age allowance, the "
        "higher one, so this is true for every unit then."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2021/188/regulation/2/made",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
    )

    def formula(benunit, period, parameters):
        cutoff = parameters(
            period
        ).gov.dwp.housing_benefit.allowances.pension_age_cutoff
        if cutoff is None:
            return np.ones(benunit.count, dtype=bool)
        # SI 2006/214 Sch 3 para 1(2)(b) keeps the higher couple rate where
        # "one member or both members" attained pensionable age before the
        # cutoff; (2)(c) gives the lower one only where both attained it on or
        # after. The regulations do not say which applies to a couple where one
        # member has not yet attained it and the other did so after the cutoff
        # (few such units remain on pension-age Housing Benefit). The
        # explanatory note to SI 2021/188 keeps the uplift only where "one or
        # more members ... attained pensionable age before 1st April 2021", so
        # such couples get the lower rate here.
        attained = benunit.members("state_pension_age_date", period)
        return benunit.any(attained < cutoff)
