from policyengine_uk.model_api import *


class ITEPAIntermediaryChapter(Enum):
    NONE = "None"
    CHAPTER_8 = "Chapter 8: workers under arrangements made by intermediaries"
    CHAPTER_9 = "Chapter 9: managed service companies"
    CHAPTER_10 = "Chapter 10: workers' services provided through intermediaries"


class owned_company_intermediary_earnings_chapter(Variable):
    value_type = Enum
    possible_values = ITEPAIntermediaryChapter
    default_value = ITEPAIntermediaryChapter.NONE
    entity = Person
    label = "owned company income made employed earnings by the intermediaries rules"
    documentation = (
        "The chapter of Part 2 of the Income Tax (Earnings and Pensions) Act "
        "2003, if any, under which income the person derives from the company "
        "in which they stand as sole owner or partner is employed earnings "
        "(the IR35 and managed service company rules)."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003 Part 2 Chapters 8-10",
        href="https://www.legislation.gov.uk/ukpga/2003/1/part/2",
    )
