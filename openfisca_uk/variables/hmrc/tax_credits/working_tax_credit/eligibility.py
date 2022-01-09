from openfisca_uk.model_api import *

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

        first_condition = person("is_in_work", period)

        

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