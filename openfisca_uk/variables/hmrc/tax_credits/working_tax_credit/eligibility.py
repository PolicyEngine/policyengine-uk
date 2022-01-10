from openfisca_uk.model_api import *

class is_work_disadvantaged(Variable):
    label = "Has a disadvantage when looking for work"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        eligible_benefits = parameters(period).hmrc.tax_credits.working_tax_credits.eligibility.work_disadvantage
        return np.any([person(benefit, period) > 0 for benefit in eligible_benefits])

class in_wtc_qualifying_remunerative_work(Variable):
    label = "In qualifying remunerative work"
    documentation = "Whether this person is in qualifying remunerative work"
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/uksi/2002/2005/part/2/crossheading/basic-element"

    def formula(person, period, parameters):
        """
        The Tax Credits Act 2002 specifies that a benefit unit is eligible
        if either of them are in "qualifying remunerative work", leaving the
        definitions up to future regulations. The relevant regulations are in
        The Working Tax Credit (Entitlement and Maximum Rate) Regulations 2002,
        and these specify that a person is in "qualifying remunerative work" if,
        and only if, they satisfy four conditions. The first two are modelled here;
        the third requires that the work continues for at least four weeks and 
        the fourth is that the work is remunerative.
        """
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit.eligibility

        in_work = person("is_in_work", period)
        claim_is_joint = person.benunit("is_joint_benunit", period)
        age = person("age", period)
        hours = person("weekly_hours", period)
        disadvantaged = person("is_work_disadvantaged", period)
        has_children = person.benunit("benunit_has_children_or_qyp", period)

        lower_hours = hours >= wtc.work_requirements.lower
        couple_hours = person.benunit.sum(hours) >= wtc.work_requirements.couple
        standard_hours = hours >= wtc.work_requirements.standard

        young = (age >= wtc.age_groups.lower) & (age < wtc.age_groups.middle)
        middle_aged = (age >= wtc.age_groups.middle) & (age < wtc.age_groups.upper)
        old = age >= wtc.age_groups.upper

        meets_hours_requirement = (
            (
                ~claim_is_joint
                & (
                    (young & lower_hours & (disadvantaged | has_children))
                    | (middle_aged & standard_hours)
                    | (old & lower_hours)
                )
            )
            | (
                (claim_is_joint & ~has_children)
                & (
                    (young & lower_hours & disadvantaged)
                    | (middle_aged & standard_hours)
                    | (old & couple_hours)
                )
            )
            | (
                (claim_is_joint & has_children)
                & (
                    (person.benunit.any(lower_hours) & couple_hours)
                    | (lower_hours & disadvantaged)
                    | (old & lower_hours)
                )
            )
        )

        return in_work & meets_hours_requirement

        

class is_wtc_eligible(Variable):
    label = "Eligible for WTC"
    documentation = "Whether this benefit unit is eligible for Working Tax Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/10",
        "https://www.legislation.gov.uk/uksi/2002/2005/part/2/crossheading/basic-element",
    )

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("in_wtc_qualifying_remunerative_work", period))