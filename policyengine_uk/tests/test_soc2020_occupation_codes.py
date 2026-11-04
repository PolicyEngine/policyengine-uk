"""The SOC 2020 code maps beside the occupation enums.

Datasets turn survey codes into members, and crosswalks keyed on SOC codes turn
members back into codes, through SOC2020_MAJOR_GROUP_CODES and
SOC2020_SUB_MAJOR_GROUP_CODES. These tests pin each map to the official codes
(ONS SOC 2020 Volume 1, Table 2), so a reordered, renamed or inserted member
fails here.
"""

from policyengine_uk.variables.household.income.soc2020_major_group import (
    SOC2020_MAJOR_GROUP_CODES,
    SOC2020MajorGroup,
)
from policyengine_uk.variables.household.income.soc2020_sub_major_group import (
    SOC2020_SUB_MAJOR_GROUP_CODES,
    SOC2020SubMajorGroup,
)

MAJOR_GROUP_CODES = [1, 2, 3, 4, 5, 6, 7, 8, 9]
SUB_MAJOR_GROUP_CODES = [
    11, 12, 21, 22, 23, 24, 31, 32, 33, 34, 35, 41, 42,
    51, 52, 53, 54, 61, 62, 63, 71, 72, 81, 82, 91, 92,
]  # fmt: skip


def _coded_members(enum) -> list[str]:
    return [member.name for member in enum if member.name != "NONE"]


def test_major_group_map_gives_each_member_its_code_in_member_order():
    assert list(SOC2020_MAJOR_GROUP_CODES) == _coded_members(SOC2020MajorGroup)
    assert list(SOC2020_MAJOR_GROUP_CODES.values()) == MAJOR_GROUP_CODES


def test_sub_major_group_map_gives_each_member_its_code_in_member_order():
    assert list(SOC2020_SUB_MAJOR_GROUP_CODES) == _coded_members(SOC2020SubMajorGroup)
    assert list(SOC2020_SUB_MAJOR_GROUP_CODES.values()) == SUB_MAJOR_GROUP_CODES


def test_sub_major_groups_cover_the_major_groups_by_first_digit():
    first_digits = {code // 10 for code in SOC2020_SUB_MAJOR_GROUP_CODES.values()}
    assert first_digits == set(SOC2020_MAJOR_GROUP_CODES.values())
