from policyengine_uk.model_api import *
from policyengine_uk.utils.housing_benefit import calendar_dates
from policyengine_uk.utils.housing_benefit_non_dependants import (
    postponed_non_dep_increases,
)


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/59",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/57",
    )

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependants residing with the claimant
        # (HB Regs 2006 reg 74; HB (SPC) Regs 2006 reg 55). Joint occupiers,
        # boarders, lodgers and the landlord's household are not
        # non-dependants (reg 3(2)(d)-(e), 3(4)). A non-dependant of more
        # than one joint occupier is apportioned between them by their shares
        # of the payments (reg 74(5); SPC reg 55(5)), so each family liable
        # for the household's rent bears its share; a boarder or lodger bears
        # none.
        person = benunit.members
        deductions = person(
            "household_benefits_individual_non_dep_deduction", period
        ) * person("is_non_dependant_of_household_head", period)
        # Study-period and non-working summer students are exempt for every
        # claimant. Pension-age / age-65 exceptions depend on this claimant,
        # not on whether any unrelated pensioner lives in the household.
        student = person("housing_benefit_non_dep_full_time_student", period)
        study = person("housing_benefit_non_dep_period_of_study", period)
        summer = person("housing_benefit_non_dep_summer_vacation", period)
        works = person("housing_benefit_remunerative_work", period)
        deductions *= ~(student & (study | (summer & ~works)))
        p = parameters(
            period
        ).gov.dwp.housing_benefit.non_dep_deduction.additional_exceptions
        adult = person("is_claimant_or_partner", period)
        age_65 = benunit.any(adult & (person("age", period) >= p.former_pension_age))
        state_pension_age = benunit.any(adult & person("is_SP_age", period))
        pension = benunit("housing_benefit_pension_age_regulations_apply", period)
        country = benunit.household("country", period)
        ni = country == country.possible_values.NORTHERN_IRELAND
        after_age_change = benunit(
            "housing_benefit_assessment_date", period
        ) >= calendar_dates(p.age_condition_removed)
        full_exemption = where(
            pension, where(ni | ~after_age_change, age_65, True), state_pension_age
        )
        total = benunit.max(person.household.sum(deductions))
        all_students = benunit.max(person.household.sum(deductions * student))
        total -= full_exemption * all_students
        postponed = postponed_non_dep_increases(
            benunit,
            period,
            deductions,
            full_exemption,
            student,
            pension & (after_age_change | age_65),
            p.postponement_weeks,
        )
        share = benunit("share_of_household_rent", period)
        return share * max_(total - postponed, 0)
