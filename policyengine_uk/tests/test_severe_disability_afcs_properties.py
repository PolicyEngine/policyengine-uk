"""Property-based tests for the severe disability test and Armed Forces
Compensation Scheme payments.

Law:
- Child Tax Credit Regulations 2002 (SI 2002/2007) reg 8(3)-(5): a person is
  severely disabled if the DLA care component is payable at the highest rate,
  the PIP daily living component at the enhanced rate, or "an armed forces
  independence payment is payable in respect of him".
- Working Tax Credit (Entitlement and Maximum Rate) Regulations 2002 reg
  17(2)-(4): the same, plus Attendance Allowance at the higher rate.
- Armed forces independence payment is one of the injury benefits in the Armed
  Forces and Reserve Forces (Compensation Scheme) Order 2011 art 15(1), next to
  lump sums, supplementary awards and guaranteed income payments. Only it is
  named; the afcs variables hold the other payments.

Invariants, for any generated population of families:

1. Differential: is_severely_disabled_for_benefits equals the tax credit
   condition (CTC reg 8(3)-(5) with WTC reg 17(2)'s higher-rate Attendance
   Allowance) recomputed here from the DLA care, PIP daily living and
   Attendance Allowance categories and armed forces independence payment.
2. Metamorphic: changing every person's AFCS payment (to zero or another
   amount) changes neither the severe disability test nor the amounts that read
   it: the UC higher rate disabled child addition, the CTC severely disabled
   child element and the WTC severe disability element. The legacy severe
   disability premium, which reads its own qualifying-benefit list
   (receives_severe_disability_premium_qualifying_benefit) rather than this
   flag, is checked the same way as an independent case: its list also names
   armed forces independence payment and no other AFCS payment.
3. Monotone: adding armed forces independence payment to a person never turns
   the severe disability test off, and turns it on.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

UC_YEAR = 2025
TAX_CREDIT_YEAR = 2024
YEARS = (TAX_CREDIT_YEAR, UC_YEAR)
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
DLA_CARE = ["NONE", "LOWER", "MIDDLE", "HIGHER"]
ATTENDANCE_ALLOWANCE = ["NONE", "LOWER", "HIGHER"]
PIP_DAILY_LIVING = ["NONE", "STANDARD", "ENHANCED"]
amounts = st.one_of(st.just(0.0), st.floats(1, 40_000))


@st.composite
def people(draw, ages):
    return dict(
        age=draw(ages),
        dla_sc_category=draw(st.sampled_from(DLA_CARE)),
        pip_dl_category=draw(st.sampled_from(PIP_DAILY_LIVING)),
        aa_category=draw(st.sampled_from(ATTENDANCE_ALLOWANCE)),
        afcs_reported=draw(amounts),
        armed_forces_independence_payment=draw(
            st.one_of(st.just(0.0), st.just(0.0), st.floats(1, 15_000))
        ),
    )


@st.composite
def families(draw):
    return dict(
        adults=draw(st.lists(people(st.integers(25, 60)), min_size=1, max_size=2)),
        # 16 to 18 year olds are in non-advanced education, so qualifying young
        # persons for both UC and CTC; younger ones are children. A 19-year-old
        # would also need their course to have started before 19, so none is
        # drawn.
        dependants=draw(st.lists(people(st.integers(0, 18)), max_size=2)),
    )


populations = st.lists(families(), min_size=10, max_size=20)


def situation(units, afcs=None, afip=None):
    """Build a situation; afcs/afip map a person name to a replacement."""
    people_, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for role, members in (("a", unit["adults"]), ("d", unit["dependants"])):
            for j, person in enumerate(members):
                name = f"{role}{i}_{j}"
                values = dict(person)
                if afcs is not None:
                    values["afcs_reported"] = afcs(name, values["afcs_reported"])
                if afip is not None:
                    values["armed_forces_independence_payment"] = afip(
                        name, values["armed_forces_independence_payment"]
                    )
                if role == "a":
                    values["is_parent"] = bool(unit["dependants"])
                elif values["age"] >= 16:
                    values["is_in_non_advanced_education"] = True
                people_[name] = {k: {y: v for y in YEARS} for k, v in values.items()}
                names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "is_CTC_eligible": {TAX_CREDIT_YEAR: True},
            "is_WTC_eligible": {TAX_CREDIT_YEAR: True},
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people_, "benunits": benunits, "households": households}


def reference_severely_disabled(units):
    """CTC Regs 2002 reg 8(3)-(5) and WTC Regs 2002 reg 17(2)-(4), from the
    inputs alone."""
    flags = []
    for unit in units:
        for person in unit["adults"] + unit["dependants"]:
            flags.append(
                person["dla_sc_category"] == "HIGHER"
                or person["pip_dl_category"] == "ENHANCED"
                or person["aa_category"] == "HIGHER"
                or person["armed_forces_independence_payment"] > 0
            )
    return np.array(flags)


def outputs(sim):
    return dict(
        flag=sim.calculate("is_severely_disabled_for_benefits", UC_YEAR),
        uc_addition=sim.calculate(
            "uc_individual_severely_disabled_child_element", UC_YEAR
        ),
        ctc_element=sim.calculate(
            "CTC_severely_disabled_child_element", TAX_CREDIT_YEAR
        ),
        wtc_element=sim.calculate("WTC_severely_disabled_element", TAX_CREDIT_YEAR),
        premium=sim.calculate("severe_disability_premium", UC_YEAR),
    )


@PROPERTY_SETTINGS
@given(populations)
def test_severe_disability_matches_the_tax_credit_condition(units):
    sim = Simulation(situation=situation(units))
    flag = np.asarray(sim.calculate("is_severely_disabled_for_benefits", UC_YEAR))
    np.testing.assert_array_equal(flag, reference_severely_disabled(units))


@PROPERTY_SETTINGS
@given(populations, st.data())
def test_afcs_payments_never_change_severe_disability(units, data):
    replacements = {}

    def new_afcs(name, _):
        if name not in replacements:
            replacements[name] = data.draw(amounts, label=f"afcs {name}")
        return replacements[name]

    before = outputs(Simulation(situation=situation(units)))
    no_afcs = outputs(Simulation(situation=situation(units, afcs=lambda n, v: 0.0)))
    other_afcs = outputs(Simulation(situation=situation(units, afcs=new_afcs)))
    for name, value in before.items():
        np.testing.assert_allclose(no_afcs[name], value, atol=1e-6, err_msg=name)
        np.testing.assert_allclose(other_afcs[name], value, atol=1e-6, err_msg=name)


@PROPERTY_SETTINGS
@given(populations, st.floats(1, 15_000))
def test_armed_forces_independence_payment_confers_severe_disability(units, amount):
    before = np.asarray(
        Simulation(situation=situation(units)).calculate(
            "is_severely_disabled_for_benefits", UC_YEAR
        )
    )
    after = np.asarray(
        Simulation(situation=situation(units, afip=lambda n, v: amount)).calculate(
            "is_severely_disabled_for_benefits", UC_YEAR
        )
    )
    assert after.all()
    assert (after >= before).all()
