import numpy as np

from policyengine_uk import Simulation
from policyengine_uk.scenarios import abolish_benefit_cap

BENEFIT_CAP_FAMILY = {
    "people": {
        "parent1": {"age": {2026: 30}, "employment_income": {2026: 0}},
        "parent2": {"age": {2026: 28}, "employment_income": {2026: 0}},
        "child1": {"age": {2026: 6}},
        "child2": {"age": {2026: 3}},
        "child3": {"age": {2026: 1}},
    },
    "benunits": {
        "family": {"members": ["parent1", "parent2", "child1", "child2", "child3"]}
    },
    "households": {
        "home": {
            "members": ["parent1", "parent2", "child1", "child2", "child3"],
            "rent": {2026: 24_000},
        }
    },
}


class TestAbolishBenefitCapScenario:
    def test_removes_benefit_cap_reduction(self):
        baseline = Simulation(situation=BENEFIT_CAP_FAMILY)
        reformed = Simulation(
            situation=BENEFIT_CAP_FAMILY, scenario=abolish_benefit_cap
        )

        baseline_reduction = baseline.calculate("benefit_cap_reduction", 2026)
        baseline_uc = baseline.calculate("universal_credit", 2026)
        reformed_cap = reformed.calculate("benefit_cap", 2026)
        reformed_reduction = reformed.calculate("benefit_cap_reduction", 2026)
        reformed_uc = reformed.calculate("universal_credit", 2026)
        reformed_uc_pre_cap = reformed.calculate(
            "universal_credit_pre_benefit_cap", 2026
        )

        assert baseline_reduction[0] > 0
        assert np.isfinite(baseline.calculate("benefit_cap", 2026)[0])
        assert np.isinf(reformed_cap[0])
        assert reformed_reduction.tolist() == [0.0]
        assert reformed_uc.tolist() == reformed_uc_pre_cap.tolist()
        assert reformed_uc[0] > baseline_uc[0]
