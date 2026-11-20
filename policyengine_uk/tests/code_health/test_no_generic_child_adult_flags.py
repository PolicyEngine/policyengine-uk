"""No model code may read the deprecated generic child and adult variables.

UK law has no single definition of a child or an adult: each programme sets
its own (Child Benefit, Universal Credit, tax credits, Pension Credit, the
legacy means-tested benefits, student support, ...), and statistics follow
the Households Below Average Income definitions. The generic variables below
use age-18 cut-offs with no legal basis. They are kept, with their original
formulas, only because downstream packages still read them.
"""

import re
from pathlib import Path

import pytest

from policyengine_uk.system import system

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

DEPRECATED = {
    "is_child",
    "is_adult",
    "num_children",
    "num_adults",
    "benunit_count_children",
    "benunit_count_adults",
    "eldest_child_age",
    "youngest_child_age",
    "eldest_adult_age",
    "youngest_adult_age",
    "child_index",
    "is_eldest_child",
    "is_benunit_eldest_child",
    "num_disabled_children",
    "num_enhanced_disabled_children",
    "num_severely_disabled_children",
    "num_disabled_adults",
    "num_enhanced_disabled_adults",
    "num_severely_disabled_adults",
    "family_type",
    "is_WA_adult",
    "is_young_child",
    "is_older_child",
}

# A shim may read another shim, so that each keeps its original formula.
SHIM_FILES = {
    PACKAGE_ROOT / "variables" / "household" / "demographic" / f"{name}.py"
    for name in DEPRECATED
} | {
    PACKAGE_ROOT / "variables" / "household" / "demographic" / "benunit" / f"{name}.py"
    for name in DEPRECATED
}

REFERENCE = re.compile(
    r"""["'](""" + "|".join(sorted(DEPRECATED, key=len, reverse=True)) + r""")["']"""
)


def _model_files():
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if path.suffix not in (".py", ".yaml"):
            continue
        if "tests" in path.relative_to(PACKAGE_ROOT).parts:
            continue
        if path in SHIM_FILES:
            continue
        yield path


def test_shims_still_exist_for_downstream_users():
    missing = sorted(name for name in DEPRECATED if name not in system.variables)
    assert not missing, f"Deprecated variables removed too early: {missing}"


def test_shims_are_labelled_deprecated():
    unlabelled = sorted(
        name
        for name in DEPRECATED
        if "deprecated" not in (system.variables[name].label or "").lower()
    )
    assert not unlabelled, (
        f"Deprecated variables without a deprecated label: {unlabelled}"
    )


@pytest.mark.parametrize(
    "path", list(_model_files()), ids=lambda p: str(p.relative_to(PACKAGE_ROOT))
)
def test_model_code_does_not_read_generic_child_or_adult_flags(path):
    hits = sorted({m.group(1) for m in REFERENCE.finditer(path.read_text())})
    assert not hits, (
        f"{path.relative_to(PACKAGE_ROOT)} reads deprecated generic variables "
        f"{hits}. Use the programme's own legal definition, an explicit age "
        "predicate, or an HBAI variable (hbai in the name) instead."
    )
