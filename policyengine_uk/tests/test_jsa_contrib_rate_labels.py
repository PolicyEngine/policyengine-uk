"""The contributory JSA rate parameters say what they are (#2945).

New Style (contributory) JSA has two weekly rates, one for claimants aged 18
to 24 and one for those aged 25 or over
(https://www.gov.uk/jobseekers-allowance/what-youll-get). The 18-24 rate was
labelled income-based and the other "over 25", which left out claimants
aged exactly 25.
"""

from policyengine_uk.system import system

CONTRIB = system.parameters.gov.dwp.JSA.contrib


def test_the_18_to_24_rate_is_labelled_contributory_for_ages_18_to_24():
    metadata = CONTRIB.amount_18_24.metadata
    assert metadata["label"] == "Contributory JSA (18-24)"
    assert "income-based" not in metadata["label"].lower()
    assert "contributory" in CONTRIB.amount_18_24.description.lower()
    assert "18 to 24" in CONTRIB.amount_18_24.description


def test_the_older_rate_covers_claimants_aged_25_or_over():
    metadata = CONTRIB.amount_over_25.metadata
    assert metadata["label"] == "Contributory JSA (25 and over)"
    assert "25 or over" in CONTRIB.amount_over_25.description
