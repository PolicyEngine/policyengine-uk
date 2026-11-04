from policyengine_uk.model_api import *


class scottish_carer_supplement(Variable):
    value_type = float
    entity = Person
    label = "Scottish Carer Supplement"
    documentation = (
        "From 15 March 2026, Social Security Scotland pays the Scottish Carer "
        "Supplement for each award week in which Carer Support Payment is "
        "payable. The formula counts those weeks from annual amounts: it "
        "divides the larger of carer_support_payment_pre_overlap and "
        "carer_support_payment by the weekly Carer Support Payment rate, keeps"
        " any part week and caps the count at the model's 52 weeks a year. It "
        "pays the weekly supplement rate for each of those weeks, and nothing "
        "where carer_support_payment is £0, as where an overlapping benefit "
        "such as State Pension takes the payment to £0. Where the model "
        "computes the amount before the overlapping-benefit reduction, that "
        "amount comes to 52 weekly rates or nothing, so a carer whose "
        "overlapping benefit reduces the payment but leaves some keeps all 52 "
        "weeks. Where a user supplies the payment and the inputs give no "
        "amount before the reduction, the formula divides the payment by the "
        "weekly rate to count the weeks. A carer who moves to England, for "
        "example, keeps Carer Support for 13 weeks after the move. Where the "
        "cared-for person dies in that time, the carer keeps it for up to 25 "
        "weeks and 6 days in all. A move on a Sunday gives 13 complete award "
        "weeks, or up to 25 after such a death, each counted from a Sunday. A "
        "move on any other day spreads the 13 weeks over 14 award weeks. The "
        "count differs from the law in these cases, among others. Where an "
        "overlapping benefit or earnings vary within the year, the formula "
        "counts 52 weeks or none from the annual amounts, while Social Security Scotland pays the supplement only for "
        "the award weeks in which the payment stays payable. Where a user "
        "supplies a part-year payment and also sets inputs that make the "
        "person eligible in Scotland, the formula counts 52 weeks, since the "
        "model reads those inputs as a whole year. Where a user supplies a "
        "payment that an overlapping benefit has reduced, the formula counts "
        "fewer weeks than the award weeks in which that payment is payable, "
        "unless the inputs also give the amount before the reduction. Under "
        "gov.contrib.policyengine.disable_simulated_benefits, a Scottish "
        "carer's reported Carer's Allowance becomes carer_support_payment "
        "while the amount before the reduction stays the model's, so the "
        "formula counts 52 weeks for a reported carer the model finds "
        "eligible, even where the report covers only part of the year, and the"
        " weeks the report implies at each year's weekly rate for any other "
        "reported carer; the reform doesn't uprate the report, so a report of "
        "a full year counts fewer weeks in later years. Where a user supplies "
        "a part-year amount before the overlapping-benefit reduction and the "
        "person has an overlapping benefit paid all year, the model nets the "
        "annual amounts. The formula can then count no weeks, while Social "
        "Security Scotland compares the weekly amounts in each award "
        "week of the award. The formula also counts part weeks where a "
        "payment falls between whole numbers of weekly rates. Such a payment "
        "arises for an award that starts or ends during an award week or "
        "spans an April uprating. Social Security Scotland instead pays a "
        "whole weekly supplement for each award week in which Carer Support "
        "Payment is payable. The supplement is a "
        "component of Carer Support separate from the Carer Support Payment "
        "component. Pension Credit, Housing Benefit and Scottish Council Tax "
        "Reduction, at pension age and working age, do not count it as income;"
        " it is taxable."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/2",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/14A",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/42",
        "https://www.legislation.gov.uk/uksi/2026/246/article/17/made",
        "https://www.legislation.gov.uk/uksi/2026/246/article/20/made",
        "https://www.legislation.gov.uk/uksi/2026/246/article/21/made",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
        "https://www.legislation.gov.uk/uksi/2026/93/made",
    ]

    def formula(person, period, parameters):
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        payable = person("carer_support_payment", period)
        # The model computes the entitlement before the overlapping-benefit
        # reduction as 52 weekly rates or nothing; a supplied payment with no
        # such entitlement gives its own weeks.
        amount = max_(person("carer_support_payment_pre_overlap", period), payable)
        # 52 weekly rates in the amount's dtype, the value the model stores for
        # a full year's entitlement, so that a full year counts exactly 52
        # weeks. The share of the year is the award weeks over 52.
        full_year = np.asarray(csp.rate * WEEKS_IN_YEAR, dtype=amount.dtype)
        has_rate = full_year > 0
        share = where(has_rate, amount / where(has_rate, full_year, 1), 0)
        # The model counts 52 award weeks in a year.
        year_of_supplement = csp.supplement * WEEKS_IN_YEAR
        return where(payable > 0, year_of_supplement * min_(share, 1), 0)
