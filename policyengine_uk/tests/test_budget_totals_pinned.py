"""household_tax, household_benefits and household_net_income stay exact.

household_tax and household_benefits read their terms from programs.yaml.
EXPECTED holds the three totals for thirteen hand-built households in four
years under four reforms, computed with the lists that the formula modules
held as literals at commit 2da212abcf2086337fc088a4a1236f4ae7b6af63. The
reforms switch on gov.contrib.abolish_council_tax, the two
gov.contrib.benefit_uprating rates, and a flat basic income, which the
uprating leaves out. The test compares with exact equality, because the
totals add the same float32 terms in the same order.
"""

import pytest

from policyengine_uk import Simulation

YEARS = (2023, 2025, 2026, 2028)

REFORMS = {
    "baseline": {},
    "abolish_council_tax": {"gov.contrib.abolish_council_tax": True},
    "uprating": {
        "gov.contrib.benefit_uprating.all": 0.05,
        "gov.contrib.benefit_uprating.non_sp": 0.1,
    },
    "abolish_uprating_basic_income": {
        "gov.contrib.abolish_council_tax": True,
        "gov.contrib.benefit_uprating.all": -0.03,
        "gov.contrib.benefit_uprating.non_sp": 0.07,
        "gov.contrib.ubi_center.basic_income.amount.flat": 40,
    },
}

# Each household: region, tenure, rent, council tax, main residence value,
# and its people.
HOUSEHOLDS = {
    "single_renter_london": dict(
        region="LONDON",
        tenure_type="RENT_PRIVATELY",
        rent=14_400,
        council_tax=1_500,
        people={"a": dict(age=30, employment_income=25_000)},
    ),
    "couple_two_children_uc": dict(
        region="NORTH_WEST",
        tenure_type="RENT_FROM_COUNCIL",
        rent=6_000,
        council_tax=1_400,
        would_claim_uc=True,
        people={
            "a": dict(age=34, employment_income=18_000),
            "b": dict(age=32),
            "c1": dict(age=3),
            "c2": dict(age=7),
        },
    ),
    "pensioner_couple": dict(
        region="SOUTH_WEST",
        tenure_type="OWNED_OUTRIGHT",
        council_tax=2_100,
        people={
            "a": dict(age=72, state_pension_reported=11_000),
            "b": dict(age=69, state_pension_reported=9_000),
        },
    ),
    "scottish_lone_parent": dict(
        region="SCOTLAND",
        tenure_type="RENT_FROM_HA",
        rent=5_200,
        council_tax=1_100,
        would_claim_uc=True,
        people={
            "a": dict(age=26, employment_income=9_000),
            "c1": dict(age=2),
        },
    ),
    "welsh_working_family": dict(
        region="WALES",
        tenure_type="OWNED_WITH_MORTGAGE",
        council_tax=1_800,
        people={
            "a": dict(age=38, employment_income=42_000),
            "b": dict(age=36, employment_income=21_000),
            "c1": dict(age=3),
        },
    ),
    "northern_ireland_owner": dict(
        region="NORTHERN_IRELAND",
        tenure_type="OWNED_OUTRIGHT",
        people={
            "a": dict(age=50, self_employment_income=38_000),
            "b": dict(age=48, employment_income=15_000),
        },
    ),
    "high_earner_south_east": dict(
        region="SOUTH_EAST",
        tenure_type="OWNED_WITH_MORTGAGE",
        council_tax=3_200,
        people={
            "a": dict(age=45, employment_income=160_000),
            "c1": dict(age=10),
            "c2": dict(age=13),
        },
    ),
    "unemployed_contributory_jsa": dict(
        region="WEST_MIDLANDS",
        tenure_type="RENT_PRIVATELY",
        rent=7_800,
        council_tax=1_300,
        people={"a": dict(age=27, jsa_contrib_reported=3_000)},
    ),
    "esa_and_reported_benefits": dict(
        region="NORTH_EAST",
        tenure_type="RENT_FROM_COUNCIL",
        rent=5_000,
        council_tax=1_200,
        people={
            "a": dict(age=55, esa_contrib_reported=5_000, iidb_reported=2_000),
            "b": dict(age=52, employment_income=12_000, afcs_reported=1_500),
        },
    ),
    "scottish_pensioner": dict(
        region="SCOTLAND",
        tenure_type="OWNED_OUTRIGHT",
        council_tax=1_600,
        people={"a": dict(age=81, state_pension_reported=12_500)},
    ),
    "large_family_yorkshire": dict(
        region="YORKSHIRE",
        tenure_type="RENT_PRIVATELY",
        rent=9_600,
        council_tax=1_500,
        would_claim_uc=True,
        people={
            "a": dict(age=40, employment_income=24_000),
            "b": dict(age=39),
            "c1": dict(age=1),
            "c2": dict(age=4),
            "c3": dict(age=9),
            "c4": dict(age=12),
        },
    ),
    "east_of_england_mixed": dict(
        region="EAST_OF_ENGLAND",
        tenure_type="OWNED_WITH_MORTGAGE",
        council_tax=2_000,
        people={
            "a": dict(age=63, employment_income=30_000, self_employment_income=8_000),
            "b": dict(age=67, state_pension_reported=10_500, bsp_reported=1_000),
        },
    ),
    # Owns a £3m main residence, so pays the High Value Council Tax
    # Surcharge from 2028.
    "london_high_value_owner": dict(
        region="LONDON",
        tenure_type="OWNED_OUTRIGHT",
        council_tax=3_800,
        main_residence_value=3_000_000,
        people={"a": dict(age=58, employment_income=180_000)},
    ),
}

HOUSEHOLD_INPUTS = (
    "region",
    "tenure_type",
    "rent",
    "council_tax",
    "main_residence_value",
)
OUTPUTS = ("household_tax", "household_benefits", "household_net_income")


def situation(year):
    """All the households above, as one situation for ``year``."""
    people, benunits, households = {}, {}, {}
    for key, spec in HOUSEHOLDS.items():
        members = []
        for person, inputs in spec["people"].items():
            name = f"{key}.{person}"
            people[name] = {var: {year: value} for var, value in inputs.items()}
            members.append(name)
        benunits[key] = {
            "members": members,
            "would_claim_uc": {year: spec.get("would_claim_uc", False)},
        }
        households[key] = {"members": members}
        for var in HOUSEHOLD_INPUTS:
            if var in spec:
                households[key][var] = {year: spec[var]}
    return {"people": people, "benunits": benunits, "households": households}


# (reform, year, household): (household_tax, household_benefits,
# household_net_income), from commit 2da212ab.
EXPECTED = {
    ("baseline", 2023, "single_renter_london"): (
        5636.60498046875,
        201.0,
        19564.39453125,
    ),
    ("baseline", 2023, "couple_two_children_uc"): (
        3044.604736328125,
        18789.482421875,
        33744.87890625,
    ),
    ("baseline", 2023, "pensioner_couple"): (2259.0, 22177.880859375, 19918.880859375),
    ("baseline", 2023, "scottish_lone_parent"): (
        1259.0,
        14060.240234375,
        21801.240234375,
    ),
    ("baseline", 2023, "welsh_working_family"): (
        14074.208984375,
        6699.0,
        55624.7890625,
    ),
    ("baseline", 2023, "northern_ireland_owner"): (8490.705078125, 600.0, 45109.296875),
    ("baseline", 2023, "high_earner_south_east"): (
        71726.2265625,
        2275.800048828125,
        90549.5703125,
    ),
    ("baseline", 2023, "unemployed_contributory_jsa"): (1459.0, 3201.0, 1742.0),
    ("baseline", 2023, "esa_and_reported_benefits"): (1359.0, 8701.0, 19342.0),
    ("baseline", 2023, "scottish_pensioner"): (
        1600.0,
        15566.208984375,
        13966.208984375,
    ),
    ("baseline", 2023, "large_family_yorkshire"): (
        5064.60498046875,
        19482.12109375,
        38417.515625,
    ),
    ("baseline", 2023, "east_of_england_mixed"): (
        9084.6044921875,
        12201.0,
        41116.39453125,
    ),
    ("baseline", 2023, "london_high_value_owner"): (
        79902.2265625,
        201.0,
        100298.7734375,
    ),
    ("baseline", 2025, "single_renter_london"): (5154.9033203125, 0.0, 19845.09765625),
    ("baseline", 2025, "couple_two_children_uc"): (
        2842.903076171875,
        18652.060546875,
        33809.16015625,
    ),
    ("baseline", 2025, "pensioner_couple"): (2274.5, 22106.400390625, 19831.900390625),
    ("baseline", 2025, "scottish_lone_parent"): (
        1274.5,
        14044.3994140625,
        21769.8984375,
    ),
    ("baseline", 2025, "welsh_working_family"): (
        12575.306640625,
        8074.599609375,
        58499.296875,
    ),
    ("baseline", 2025, "northern_ireland_owner"): (7466.703125, 0.0, 45533.296875),
    ("baseline", 2025, "high_earner_south_east"): (
        69039.1015625,
        2251.599609375,
        93212.4921875,
    ),
    ("baseline", 2025, "unemployed_contributory_jsa"): (1474.5, 3000.0, 1525.5),
    ("baseline", 2025, "esa_and_reported_benefits"): (1374.5, 8500.0, 19125.5),
    ("baseline", 2025, "scottish_pensioner"): (
        1600.0,
        14945.4013671875,
        13345.4013671875,
    ),
    ("baseline", 2025, "large_family_yorkshire"): (
        4622.9033203125,
        21061.541015625,
        40438.63671875,
    ),
    ("baseline", 2025, "east_of_england_mixed"): (
        8402.9033203125,
        11700.0,
        41297.09765625,
    ),
    ("baseline", 2025, "london_high_value_owner"): (76788.1015625, 0.0, 103211.8984375),
    ("baseline", 2026, "single_renter_london"): (
        5160.4033203125,
        100.0,
        19939.59765625,
    ),
    ("baseline", 2026, "couple_two_children_uc"): (
        2848.403076171875,
        19863.220703125,
        35014.81640625,
    ),
    ("baseline", 2026, "pensioner_couple"): (2280.0, 22386.83984375, 20106.83984375),
    ("baseline", 2026, "scottish_lone_parent"): (1280.0, 14687.2802734375, 22407.28125),
    ("baseline", 2026, "welsh_working_family"): (
        12580.806640625,
        8410.099609375,
        58829.296875,
    ),
    ("baseline", 2026, "northern_ireland_owner"): (7472.203125, 0.0, 45527.796875),
    ("baseline", 2026, "high_earner_south_east"): (
        69130.6015625,
        2437.39990234375,
        93306.8046875,
    ),
    ("baseline", 2026, "unemployed_contributory_jsa"): (1480.0, 3100.0, 1620.0),
    ("baseline", 2026, "esa_and_reported_benefits"): (1380.0, 8600.0, 19220.0),
    ("baseline", 2026, "scottish_pensioner"): (1600.0, 15286.47265625, 13686.47265625),
    ("baseline", 2026, "large_family_yorkshire"): (
        4628.4033203125,
        29562.759765625,
        48934.35546875,
    ),
    ("baseline", 2026, "east_of_england_mixed"): (
        8408.4033203125,
        11800.0,
        41391.59765625,
    ),
    ("baseline", 2026, "london_high_value_owner"): (
        76793.6015625,
        100.0,
        103306.3984375,
    ),
    ("baseline", 2028, "single_renter_london"): (5160.4033203125, 0.0, 19839.59765625),
    ("baseline", 2028, "couple_two_children_uc"): (
        2848.403076171875,
        21507.8984375,
        36659.49609375,
    ),
    ("baseline", 2028, "pensioner_couple"): (2280.0, 22573.3203125, 20293.3203125),
    ("baseline", 2028, "scottish_lone_parent"): (
        1280.0,
        15792.3837890625,
        23512.3828125,
    ),
    ("baseline", 2028, "welsh_working_family"): (
        12580.806640625,
        8973.591796875,
        59392.7890625,
    ),
    ("baseline", 2028, "northern_ireland_owner"): (7472.203125, 0.0, 45527.796875),
    ("baseline", 2028, "high_earner_south_east"): (
        69294.6015625,
        2501.4619140625,
        93206.8671875,
    ),
    ("baseline", 2028, "unemployed_contributory_jsa"): (1480.0, 3000.0, 1520.0),
    ("baseline", 2028, "esa_and_reported_benefits"): (1380.0, 8500.0, 19120.0),
    ("baseline", 2028, "scottish_pensioner"): (
        1600.0,
        15751.6220703125,
        14151.6220703125,
    ),
    ("baseline", 2028, "large_family_yorkshire"): (
        4628.4033203125,
        31807.14453125,
        51178.7421875,
    ),
    ("baseline", 2028, "east_of_england_mixed"): (
        8408.4033203125,
        11700.0009765625,
        41291.59765625,
    ),
    ("baseline", 2028, "london_high_value_owner"): (80293.6015625, 0.0, 99706.3984375),
    ("abolish_council_tax", 2023, "single_renter_london"): (
        4136.60498046875,
        201.0,
        21064.39453125,
    ),
    ("abolish_council_tax", 2023, "couple_two_children_uc"): (
        1644.604736328125,
        18789.482421875,
        35144.87890625,
    ),
    ("abolish_council_tax", 2023, "pensioner_couple"): (159.0, 20701.0, 20542.0),
    ("abolish_council_tax", 2023, "scottish_lone_parent"): (
        159.0,
        14060.240234375,
        22901.240234375,
    ),
    ("abolish_council_tax", 2023, "welsh_working_family"): (
        12274.208984375,
        6699.0,
        57424.7890625,
    ),
    ("abolish_council_tax", 2023, "northern_ireland_owner"): (
        8490.705078125,
        600.0,
        45109.296875,
    ),
    ("abolish_council_tax", 2023, "high_earner_south_east"): (
        68526.2265625,
        2275.800048828125,
        93749.5703125,
    ),
    ("abolish_council_tax", 2023, "unemployed_contributory_jsa"): (
        159.0,
        3201.0,
        3042.0,
    ),
    ("abolish_council_tax", 2023, "esa_and_reported_benefits"): (
        159.0,
        8701.0,
        20542.0,
    ),
    ("abolish_council_tax", 2023, "scottish_pensioner"): (
        0.0,
        14211.51171875,
        14211.51171875,
    ),
    ("abolish_council_tax", 2023, "large_family_yorkshire"): (
        3564.60498046875,
        19482.12109375,
        39917.515625,
    ),
    ("abolish_council_tax", 2023, "east_of_england_mixed"): (
        7084.6044921875,
        12201.0,
        43116.39453125,
    ),
    ("abolish_council_tax", 2023, "london_high_value_owner"): (
        76102.2265625,
        201.0,
        104098.7734375,
    ),
    ("abolish_council_tax", 2025, "single_renter_london"): (
        3654.903076171875,
        0.0,
        21345.09765625,
    ),
    ("abolish_council_tax", 2025, "couple_two_children_uc"): (
        1442.903076171875,
        18652.060546875,
        35209.16015625,
    ),
    ("abolish_council_tax", 2025, "pensioner_couple"): (174.5, 20200.0, 20025.5),
    ("abolish_council_tax", 2025, "scottish_lone_parent"): (
        174.5,
        14044.3994140625,
        22869.8984375,
    ),
    ("abolish_council_tax", 2025, "welsh_working_family"): (
        10775.306640625,
        8074.599609375,
        60299.296875,
    ),
    ("abolish_council_tax", 2025, "northern_ireland_owner"): (
        7466.703125,
        0.0,
        45533.296875,
    ),
    ("abolish_council_tax", 2025, "high_earner_south_east"): (
        65839.1015625,
        2251.599609375,
        96412.4921875,
    ),
    ("abolish_council_tax", 2025, "unemployed_contributory_jsa"): (
        174.5,
        3000.0,
        2825.5,
    ),
    ("abolish_council_tax", 2025, "esa_and_reported_benefits"): (
        174.5,
        8500.0,
        20325.5,
    ),
    ("abolish_council_tax", 2025, "scottish_pensioner"): (
        0.0,
        13428.2763671875,
        13428.2763671875,
    ),
    ("abolish_council_tax", 2025, "large_family_yorkshire"): (
        3122.903076171875,
        21061.541015625,
        41938.63671875,
    ),
    ("abolish_council_tax", 2025, "east_of_england_mixed"): (
        6402.9033203125,
        11700.0,
        43297.09765625,
    ),
    ("abolish_council_tax", 2025, "london_high_value_owner"): (
        72988.1015625,
        0.0,
        107011.8984375,
    ),
    ("abolish_council_tax", 2026, "single_renter_london"): (
        3660.403076171875,
        100.0,
        21439.59765625,
    ),
    ("abolish_council_tax", 2026, "couple_two_children_uc"): (
        1448.403076171875,
        19863.220703125,
        36414.81640625,
    ),
    ("abolish_council_tax", 2026, "pensioner_couple"): (180.0, 20300.0, 20120.0),
    ("abolish_council_tax", 2026, "scottish_lone_parent"): (
        180.0,
        14687.2802734375,
        23507.28125,
    ),
    ("abolish_council_tax", 2026, "welsh_working_family"): (
        10780.806640625,
        8410.099609375,
        60629.296875,
    ),
    ("abolish_council_tax", 2026, "northern_ireland_owner"): (
        7472.203125,
        0.0,
        45527.796875,
    ),
    ("abolish_council_tax", 2026, "high_earner_south_east"): (
        65930.6015625,
        2437.39990234375,
        96506.8046875,
    ),
    ("abolish_council_tax", 2026, "unemployed_contributory_jsa"): (
        180.0,
        3100.0,
        2920.0,
    ),
    ("abolish_council_tax", 2026, "esa_and_reported_benefits"): (
        180.0,
        8600.0,
        20420.0,
    ),
    ("abolish_council_tax", 2026, "scottish_pensioner"): (
        0.0,
        13700.916015625,
        13700.916015625,
    ),
    ("abolish_council_tax", 2026, "large_family_yorkshire"): (
        3128.403076171875,
        29562.759765625,
        50434.35546875,
    ),
    ("abolish_council_tax", 2026, "east_of_england_mixed"): (
        6408.4033203125,
        11800.0,
        43391.59765625,
    ),
    ("abolish_council_tax", 2026, "london_high_value_owner"): (
        72993.6015625,
        100.0,
        107106.3984375,
    ),
    ("abolish_council_tax", 2028, "single_renter_london"): (
        3660.403076171875,
        0.0,
        21339.59765625,
    ),
    ("abolish_council_tax", 2028, "couple_two_children_uc"): (
        1448.403076171875,
        21507.8984375,
        38059.49609375,
    ),
    ("abolish_council_tax", 2028, "pensioner_couple"): (
        180.0,
        20473.3203125,
        20293.3203125,
    ),
    ("abolish_council_tax", 2028, "scottish_lone_parent"): (
        180.0,
        15792.3837890625,
        24612.3828125,
    ),
    ("abolish_council_tax", 2028, "welsh_working_family"): (
        10780.806640625,
        8973.591796875,
        61192.7890625,
    ),
    ("abolish_council_tax", 2028, "northern_ireland_owner"): (
        7472.203125,
        0.0,
        45527.796875,
    ),
    ("abolish_council_tax", 2028, "high_earner_south_east"): (
        66094.6015625,
        2501.4619140625,
        96406.8671875,
    ),
    ("abolish_council_tax", 2028, "unemployed_contributory_jsa"): (
        180.0,
        3000.0,
        2820.0,
    ),
    ("abolish_council_tax", 2028, "esa_and_reported_benefits"): (
        180.0,
        8500.0,
        20320.0,
    ),
    ("abolish_council_tax", 2028, "scottish_pensioner"): (
        0.0,
        14151.6220703125,
        14151.6220703125,
    ),
    ("abolish_council_tax", 2028, "large_family_yorkshire"): (
        3128.403076171875,
        31807.14453125,
        52678.7421875,
    ),
    ("abolish_council_tax", 2028, "east_of_england_mixed"): (
        6408.4033203125,
        11700.0009765625,
        43291.59765625,
    ),
    ("abolish_council_tax", 2028, "london_high_value_owner"): (
        72993.6015625,
        0.0,
        107006.3984375,
    ),
    ("uprating", 2023, "single_renter_london"): (
        5636.60498046875,
        231.14999389648438,
        19594.544921875,
    ),
    ("uprating", 2023, "couple_two_children_uc"): (
        3044.604736328125,
        21607.90625,
        36563.30078125,
    ),
    ("uprating", 2023, "pensioner_couple"): (2259.0, 23504.5625, 21245.5625),
    ("uprating", 2023, "scottish_lone_parent"): (
        1259.0,
        16169.2763671875,
        23910.27734375,
    ),
    ("uprating", 2023, "welsh_working_family"): (
        14074.208984375,
        7703.85009765625,
        56629.640625,
    ),
    ("uprating", 2023, "northern_ireland_owner"): (8490.705078125, 690.0, 45199.296875),
    ("uprating", 2023, "high_earner_south_east"): (
        71726.2265625,
        2617.170166015625,
        90890.9453125,
    ),
    ("uprating", 2023, "unemployed_contributory_jsa"): (
        1459.0,
        3681.14990234375,
        2222.14990234375,
    ),
    ("uprating", 2023, "esa_and_reported_benefits"): (
        1359.0,
        10006.150390625,
        20647.150390625,
    ),
    ("uprating", 2023, "scottish_pensioner"): (1600.0, 16651.140625, 15051.140625),
    ("uprating", 2023, "large_family_yorkshire"): (
        5064.60498046875,
        22404.439453125,
        41339.83203125,
    ),
    ("uprating", 2023, "east_of_england_mixed"): (
        9084.6044921875,
        12981.150390625,
        41896.54296875,
    ),
    ("uprating", 2023, "london_high_value_owner"): (
        79902.2265625,
        231.14999389648438,
        100328.9296875,
    ),
    ("uprating", 2025, "single_renter_london"): (5154.9033203125, 0.0, 19845.09765625),
    ("uprating", 2025, "couple_two_children_uc"): (
        2842.903076171875,
        21449.87109375,
        36606.96875,
    ),
    ("uprating", 2025, "pensioner_couple"): (2274.5, 23422.359375, 21147.859375),
    ("uprating", 2025, "scottish_lone_parent"): (
        1274.5,
        16151.0595703125,
        23876.55859375,
    ),
    ("uprating", 2025, "welsh_working_family"): (
        12575.306640625,
        9285.7900390625,
        59710.484375,
    ),
    ("uprating", 2025, "northern_ireland_owner"): (7466.703125, 0.0, 45533.296875),
    ("uprating", 2025, "high_earner_south_east"): (
        69039.1015625,
        2589.339599609375,
        93550.2421875,
    ),
    ("uprating", 2025, "unemployed_contributory_jsa"): (1474.5, 3450.0, 1975.5),
    ("uprating", 2025, "esa_and_reported_benefits"): (1374.5, 9775.0, 20400.5),
    ("uprating", 2025, "scottish_pensioner"): (1600.0, 15937.2109375, 14337.2109375),
    ("uprating", 2025, "large_family_yorkshire"): (
        4622.9033203125,
        24220.771484375,
        43597.87109375,
    ),
    ("uprating", 2025, "east_of_england_mixed"): (
        8402.9033203125,
        12405.0,
        42002.09765625,
    ),
    ("uprating", 2025, "london_high_value_owner"): (76788.1015625, 0.0, 103211.8984375),
    ("uprating", 2026, "single_renter_london"): (
        5160.4033203125,
        115.0,
        19954.59765625,
    ),
    ("uprating", 2026, "couple_two_children_uc"): (
        2848.403076171875,
        22842.703125,
        37994.30078125,
    ),
    ("uprating", 2026, "pensioner_couple"): (2280.0, 23744.865234375, 21464.865234375),
    ("uprating", 2026, "scottish_lone_parent"): (
        1280.0,
        16890.373046875,
        24610.373046875,
    ),
    ("uprating", 2026, "welsh_working_family"): (
        12580.806640625,
        9671.615234375,
        60090.8125,
    ),
    ("uprating", 2026, "northern_ireland_owner"): (7472.203125, 0.0, 45527.796875),
    ("uprating", 2026, "high_earner_south_east"): (
        69130.6015625,
        2803.009765625,
        93672.4140625,
    ),
    ("uprating", 2026, "unemployed_contributory_jsa"): (1480.0, 3565.0, 2085.0),
    ("uprating", 2026, "esa_and_reported_benefits"): (1380.0, 9890.0, 20510.0),
    ("uprating", 2026, "scottish_pensioner"): (
        1600.0,
        16329.443359375,
        14729.443359375,
    ),
    ("uprating", 2026, "large_family_yorkshire"): (
        4628.4033203125,
        33997.171875,
        53368.76953125,
    ),
    ("uprating", 2026, "east_of_england_mixed"): (
        8408.4033203125,
        12520.0,
        42111.59765625,
    ),
    ("uprating", 2026, "london_high_value_owner"): (
        76793.6015625,
        115.0,
        103321.3984375,
    ),
    ("uprating", 2028, "single_renter_london"): (5160.4033203125, 0.0, 19839.59765625),
    ("uprating", 2028, "couple_two_children_uc"): (
        2848.403076171875,
        24734.08203125,
        39885.6796875,
    ),
    ("uprating", 2028, "pensioner_couple"): (2280.0, 23959.31640625, 21679.31640625),
    ("uprating", 2028, "scottish_lone_parent"): (
        1280.0,
        18161.240234375,
        25881.240234375,
    ),
    ("uprating", 2028, "welsh_working_family"): (
        12580.806640625,
        10319.630859375,
        60738.828125,
    ),
    ("uprating", 2028, "northern_ireland_owner"): (7472.203125, 0.0, 45527.796875),
    ("uprating", 2028, "high_earner_south_east"): (
        69294.6015625,
        2876.68115234375,
        93582.0859375,
    ),
    ("uprating", 2028, "unemployed_contributory_jsa"): (1480.0, 3450.0, 1970.0),
    ("uprating", 2028, "esa_and_reported_benefits"): (1380.0, 9775.0, 20395.0),
    ("uprating", 2028, "scottish_pensioner"): (
        1600.0,
        16864.365234375,
        15264.365234375,
    ),
    ("uprating", 2028, "large_family_yorkshire"): (
        4628.4033203125,
        36578.21484375,
        55949.8125,
    ),
    ("uprating", 2028, "east_of_england_mixed"): (
        8408.4033203125,
        12405.0009765625,
        41996.59765625,
    ),
    ("uprating", 2028, "london_high_value_owner"): (80293.6015625, 0.0, 99706.3984375),
    ("abolish_uprating_basic_income", 2023, "single_renter_london"): (
        4136.60498046875,
        2289.0400390625,
        23152.43359375,
    ),
    ("abolish_uprating_basic_income", 2023, "couple_two_children_uc"): (
        1644.604736328125,
        27861.0625,
        44216.45703125,
    ),
    ("abolish_uprating_basic_income", 2023, "pensioner_couple"): (
        159.0,
        24289.0390625,
        24130.0390625,
    ),
    ("abolish_uprating_basic_income", 2023, "scottish_lone_parent"): (
        159.0,
        18782.650390625,
        27623.650390625,
    ),
    ("abolish_uprating_basic_income", 2023, "welsh_working_family"): (
        12274.208984375,
        13206.9599609375,
        63932.75,
    ),
    ("abolish_uprating_basic_income", 2023, "northern_ireland_owner"): (
        8490.705078125,
        4784.0,
        49293.296875,
    ),
    ("abolish_uprating_basic_income", 2023, "high_earner_south_east"): (
        68526.2265625,
        8606.83203125,
        100080.6015625,
    ),
    ("abolish_uprating_basic_income", 2023, "unemployed_contributory_jsa"): (
        159.0,
        5409.0400390625,
        5250.0400390625,
    ),
    ("abolish_uprating_basic_income", 2023, "esa_and_reported_benefits"): (
        159.0,
        13209.0400390625,
        25050.0390625,
    ),
    ("abolish_uprating_basic_income", 2023, "scottish_pensioner"): (
        0.0,
        15984.9716796875,
        15984.9716796875,
    ),
    ("abolish_uprating_basic_income", 2023, "large_family_yorkshire"): (
        3564.60498046875,
        32741.40625,
        53176.80078125,
    ),
    ("abolish_uprating_basic_income", 2023, "east_of_england_mixed"): (
        7084.6044921875,
        16114.0400390625,
        47029.43359375,
    ),
    ("abolish_uprating_basic_income", 2023, "london_high_value_owner"): (
        76102.2265625,
        2289.0400390625,
        106186.8203125,
    ),
    ("abolish_uprating_basic_income", 2025, "single_renter_london"): (
        3654.903076171875,
        2080.0,
        23425.09765625,
    ),
    ("abolish_uprating_basic_income", 2025, "couple_two_children_uc"): (
        1442.903076171875,
        27718.142578125,
        44275.23828125,
    ),
    ("abolish_uprating_basic_income", 2025, "pensioner_couple"): (
        174.5,
        23768.0,
        23593.5,
    ),
    ("abolish_uprating_basic_income", 2025, "scottish_lone_parent"): (
        174.5,
        18766.17578125,
        27591.67578125,
    ),
    ("abolish_uprating_basic_income", 2025, "welsh_working_family"): (
        10775.306640625,
        14637.583984375,
        66862.28125,
    ),
    ("abolish_uprating_basic_income", 2025, "northern_ireland_owner"): (
        7466.703125,
        4160.0,
        49693.296875,
    ),
    ("abolish_uprating_basic_income", 2025, "high_earner_south_east"): (
        65839.1015625,
        8581.6640625,
        102742.5546875,
    ),
    ("abolish_uprating_basic_income", 2025, "unemployed_contributory_jsa"): (
        174.5,
        5200.0,
        5025.5,
    ),
    ("abolish_uprating_basic_income", 2025, "esa_and_reported_benefits"): (
        174.5,
        13000.0,
        24825.5,
    ),
    ("abolish_uprating_basic_income", 2025, "scottish_pensioner"): (
        0.0,
        15170.4072265625,
        15170.4072265625,
    ),
    ("abolish_uprating_basic_income", 2025, "large_family_yorkshire"): (
        3122.903076171875,
        34384.0,
        55261.09765625,
    ),
    ("abolish_uprating_basic_income", 2025, "east_of_england_mixed"): (
        6402.9033203125,
        15593.0,
        47190.09765625,
    ),
    ("abolish_uprating_basic_income", 2025, "london_high_value_owner"): (
        72988.1015625,
        2080.0,
        109091.8984375,
    ),
    ("abolish_uprating_basic_income", 2026, "single_renter_london"): (
        3660.403076171875,
        2184.0,
        23523.59765625,
    ),
    ("abolish_uprating_basic_income", 2026, "couple_two_children_uc"): (
        1448.403076171875,
        28977.75,
        45529.34765625,
    ),
    ("abolish_uprating_basic_income", 2026, "pensioner_couple"): (
        180.0,
        23872.0,
        23692.0,
    ),
    ("abolish_uprating_basic_income", 2026, "scottish_lone_parent"): (
        180.0,
        19434.771484375,
        28254.771484375,
    ),
    ("abolish_uprating_basic_income", 2026, "welsh_working_family"): (
        10780.806640625,
        14986.50390625,
        67205.6953125,
    ),
    ("abolish_uprating_basic_income", 2026, "northern_ireland_owner"): (
        7472.203125,
        4160.0,
        49687.796875,
    ),
    ("abolish_uprating_basic_income", 2026, "high_earner_south_east"): (
        65930.6015625,
        8774.8955078125,
        102844.2890625,
    ),
    ("abolish_uprating_basic_income", 2026, "unemployed_contributory_jsa"): (
        180.0,
        5304.0,
        5124.0,
    ),
    ("abolish_uprating_basic_income", 2026, "esa_and_reported_benefits"): (
        180.0,
        13104.0,
        24924.0,
    ),
    ("abolish_uprating_basic_income", 2026, "scottish_pensioner"): (
        0.0,
        15453.953125,
        15453.953125,
    ),
    ("abolish_uprating_basic_income", 2026, "large_family_yorkshire"): (
        3128.403076171875,
        43225.26953125,
        64096.86328125,
    ),
    ("abolish_uprating_basic_income", 2026, "east_of_england_mixed"): (
        6408.4033203125,
        15697.0,
        47288.59765625,
    ),
    ("abolish_uprating_basic_income", 2026, "london_high_value_owner"): (
        72993.6015625,
        2184.0,
        109190.3984375,
    ),
    ("abolish_uprating_basic_income", 2028, "single_renter_london"): (
        3660.403076171875,
        2080.0,
        23419.59765625,
    ),
    ("abolish_uprating_basic_income", 2028, "couple_two_children_uc"): (
        1448.403076171875,
        30688.21484375,
        47239.8125,
    ),
    ("abolish_uprating_basic_income", 2028, "pensioner_couple"): (
        180.0,
        24052.251953125,
        23872.251953125,
    ),
    ("abolish_uprating_basic_income", 2028, "scottish_lone_parent"): (
        180.0,
        20584.078125,
        29404.078125,
    ),
    ("abolish_uprating_basic_income", 2028, "welsh_working_family"): (
        10780.806640625,
        15572.53515625,
        67791.7265625,
    ),
    ("abolish_uprating_basic_income", 2028, "northern_ireland_owner"): (
        7472.203125,
        4160.0,
        49687.796875,
    ),
    ("abolish_uprating_basic_income", 2028, "high_earner_south_east"): (
        66094.6015625,
        8841.5205078125,
        102746.9140625,
    ),
    ("abolish_uprating_basic_income", 2028, "unemployed_contributory_jsa"): (
        180.0,
        5200.0,
        5020.0,
    ),
    ("abolish_uprating_basic_income", 2028, "esa_and_reported_benefits"): (
        180.0,
        13000.0,
        24820.0,
    ),
    ("abolish_uprating_basic_income", 2028, "scottish_pensioner"): (
        0.0,
        15922.6865234375,
        15922.6865234375,
    ),
    ("abolish_uprating_basic_income", 2028, "large_family_yorkshire"): (
        3128.403076171875,
        45559.4296875,
        66431.0234375,
    ),
    ("abolish_uprating_basic_income", 2028, "east_of_england_mixed"): (
        6408.4033203125,
        15593.0009765625,
        47184.59765625,
    ),
    ("abolish_uprating_basic_income", 2028, "london_high_value_owner"): (
        72993.6015625,
        2080.0,
        109086.3984375,
    ),
}


@pytest.mark.parametrize("reform_name", list(REFORMS))
@pytest.mark.parametrize("year", YEARS)
def test_budget_totals_match_pinned_values(reform_name, year):
    sim = Simulation(situation=situation(year), reform=REFORMS[reform_name] or None)
    actual = {
        output: [float(value) for value in sim.calculate(output, year)]
        for output in OUTPUTS
    }
    mismatches = []
    for i, household in enumerate(HOUSEHOLDS):
        expected = EXPECTED[(reform_name, year, household)]
        got = tuple(actual[output][i] for output in OUTPUTS)
        if got != expected:
            mismatches.append(f"{household}: expected {expected}, got {got}")
    assert not mismatches, "\n".join(mismatches)


def test_pinned_grid_is_complete():
    assert len(HOUSEHOLDS) >= 13
    assert set(EXPECTED) == {
        (reform, year, household)
        for reform in REFORMS
        for year in YEARS
        for household in HOUSEHOLDS
    }
