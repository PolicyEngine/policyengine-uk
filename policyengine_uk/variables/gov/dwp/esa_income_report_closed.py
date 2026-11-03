from policyengine_uk.model_api import *


class esa_income_report_closed(Variable):
    value_type = bool
    entity = Person
    label = "Income-related ESA award on this person's report has ended"
    documentation = (
        "Whether the income-related ESA award on this person's report has "
        "ended, so the model leaves the report out of esa_income, "
        "esa_income_eligible and the claimant's or partner's award "
        "(claimant_or_partner_esa_income). It ends when the person's legacy "
        "benefits close (person_legacy_benefits_closed), or when the person "
        "is the claimant or partner of a family that claims Universal Credit "
        "(claims_universal_credit). A claim for Universal Credit brings the "
        "abolition of income-related ESA (Welfare Reform Act 2012 s.33(1)(b)) "
        "into force for the claimant's old style ESA award from the first day "
        "of the period claimed for, whether or not Universal Credit is "
        "awarded (SI 2013/983 art. 4(1), (2)(a), (3)(a) and (9), and the later "
        "commencement orders that extended it to further postcode districts; "
        "in Northern Ireland, Welfare Reform (Northern Ireland) Order 2015 "
        "art. 39(1)(b) and SR 2017/190 art. 6(1) to (3) and (6)). For claims "
        "from 22 July 2020 the award runs on for two weeks after that day (SI "
        "2019/1152 reg. 5), which this annual model does not represent. A "
        "contributory allowance in the award continues as new style ESA "
        "(esa_contrib). A member who is neither the claimant nor the partner, "
        "such as a non-dependent adult, claims in their own right and is not "
        "part of the family's Universal Credit claim, so the claim does not "
        "end their award. The model applies this in every year and area: the "
        "postcode districts named in the commencement orders are not "
        "modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/33",
        "https://www.legislation.gov.uk/uksi/2013/983/article/4",
        "https://www.legislation.gov.uk/uksi/2019/1152/regulation/5",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisi/2015/2006/article/39",
        "https://www.legislation.gov.uk/nisr/2017/190/article/6",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
    )

    def formula(person, period, parameters):
        claims_uc = person.benunit("claims_universal_credit", period)
        return person("person_legacy_benefits_closed", period) | (
            person("is_claimant_or_partner", period) & claims_uc
        )
