import pytest

from policyengine_uk import Simulation

# One household with a 19-year-old (fare-paying peak) and a 40-year-old, plus a
# household bus fare total to apportion.
SITUATION = {
    "people": {
        "young": {"age": {2026: 19}},
        "adult": {"age": {2026: 40}},
    },
    "benunits": {"bu": {"members": ["young", "adult"]}},
    "households": {
        "home": {
            "members": ["young", "adult"],
            "bus_fare_spending": {2026: 470},
        }
    },
}

# Allocation weights from gov.dft.bus.fare_allocation_weight_by_age: 19 -> 3.9,
# 40 -> 0.8.
YOUNG_W, ADULT_W = 3.9, 0.8
TOTAL_W = YOUNG_W + ADULT_W


class TestBusFareAgeAllocation:
    def test_allocation_splits_by_age_weight(self):
        sim = Simulation(situation=SITUATION)
        person_fare = sim.calculate("person_bus_fare_spending", 2026)
        assert person_fare[0] == pytest.approx(470 * YOUNG_W / TOTAL_W)
        assert person_fare[1] == pytest.approx(470 * ADULT_W / TOTAL_W)
        # Allocation conserves the household total.
        assert person_fare.sum() == pytest.approx(470)

    def test_baseline_has_no_relief(self):
        sim = Simulation(situation=SITUATION)
        assert sim.calculate("bus_fare_relief", 2026)[0] == pytest.approx(0)

    def test_under_22_free_fare_relieves_eligible_member(self):
        reformed = Simulation(
            situation=SITUATION,
            reform={"gov.dft.bus.young_person_fare.age_limit": {"2026": 22}},
        )
        # Only the 19-year-old is eligible; their allocated fare is relieved in
        # full (rate defaults to 0 -> free travel).
        relief = reformed.calculate("bus_fare_relief", 2026)[0]
        assert relief == pytest.approx(470 * YOUNG_W / TOTAL_W)
