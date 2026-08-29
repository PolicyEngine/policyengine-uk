"""Interim Universal Credit capital scope: corporate_wealth is not counted.

The dataset builds ``corporate_wealth`` as total private pension wealth less
current defined benefit pension wealth plus employee shares and options, UK
shares, investment ISAs and collective investments. The Universal Credit
Regulations 2013 disregard pension rights (Schedule 10 paragraph 10) but count
shares, investment ISAs and collective investments. Until the dataset build
splits pensions from the share-like components (policyengine-uk-data#452), the
UC capital test excludes the whole bundle. These tests pin that scope: the UC
list itself, the UC assessment, and the deliberate decision that nothing
outside the UC chain changes.
"""

from policyengine_uk import Simulation

YEAR = 2025


def _single_adult_household(**household_inputs):
    return {
        "people": {"person": {"age": {YEAR: 30}}},
        "benunits": {
            "benunit": {
                "members": ["person"],
                "would_claim_uc": {YEAR: True},
            }
        },
        "households": {
            "household": {
                "members": ["person"],
                **{k: {YEAR: v} for k, v in household_inputs.items()},
            }
        },
    }


def test_corporate_wealth_is_not_a_uc_capital_source():
    simulation = Simulation(situation=_single_adult_household(savings=1_000))
    parameters = simulation.tax_benefit_system.parameters
    for instant in ("2013-04-29", "2020-01-01", f"{YEAR}-01-01", "2030-01-01"):
        listed = list(
            parameters(instant).gov.dwp.universal_credit.means_test.capital.sources
        )
        assert listed == [
            "savings",
            "other_residential_property_value",
            "non_residential_property_value",
        ]


def test_uc_assessable_capital_excludes_corporate_wealth():
    simulation = Simulation(
        situation=_single_adult_household(savings=5_000, corporate_wealth=250_000)
    )
    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 5_000
    assert simulation.calculate("is_uc_eligible", YEAR)[0]
    # Below the 6,000 GBP tariff income threshold, so the pension bundle
    # neither disqualifies the claimant nor deems a tariff income.
    assert simulation.calculate("uc_tariff_income", YEAR)[0] == 0


def test_uc_still_counts_savings_and_property():
    simulation = Simulation(
        situation=_single_adult_household(
            savings=7_000,
            other_residential_property_value=6_000,
            non_residential_property_value=4_000,
            corporate_wealth=1_000_000,
        )
    )
    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 17_000
    assert not simulation.calculate("is_uc_eligible", YEAR)[0]


def test_corporate_wealth_still_feeds_wealth_and_legacy_capital_tests():
    """Scope guard: only the UC list changed in the interim fix.

    Housing Benefit keeps counting the mixed bundle (its parameter description
    documents that as an unresolved data limitation), and total_wealth includes
    corporate_wealth regardless of any means test. The follow-up that splits
    pension wealth in the dataset build should revisit the legacy lists and
    update this test.
    """
    simulation = Simulation(
        situation=_single_adult_household(savings=1_000, corporate_wealth=50_000)
    )
    assert simulation.calculate("uc_assessable_capital", YEAR)[0] == 1_000
    assert simulation.calculate("housing_benefit_assessable_capital", YEAR)[0] == 51_000
    assert simulation.calculate("total_wealth", YEAR)[0] == 51_000
