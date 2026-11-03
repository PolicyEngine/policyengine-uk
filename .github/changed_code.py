"""Say whether a pull request changes code, for pr_code_changes.yaml.

    git -c core.quotePath=false diff --name-only --no-renames -z BASE HEAD > changed
    CODE_PATHS="policyengine_uk/** ..." python3 .github/changed_code.py changed

prints ``code=true`` or ``code=false`` for ``$GITHUB_OUTPUT``. A path is code
if it matches one of ``CODE_PATHS`` (whitespace-separated): ``dir/**`` matches
every file under ``dir/``, anything else matches that one file, as in a
workflow's ``paths`` filter. An empty change list counts as code, so an
unexpected input runs the tests rather than skipping them.

When this says false, the pull request's tests are skipped and the required
"Test / Result" check passes without running anything, so a false negative
would let untested code through: it errs towards true.

Standard library only.
"""

import os
import sys


def is_code(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if pattern.endswith("/**"):
            if path.startswith(pattern[:-2]):
                return True
        elif path == pattern:
            return True
    return False


def changes_code(changed: list[str], patterns: list[str]) -> bool:
    return not changed or any(is_code(path, patterns) for path in changed)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    patterns = os.environ.get("CODE_PATHS", "").split()
    if not patterns or any("*" in p and not p.endswith("/**") for p in patterns):
        print(f"CODE_PATHS must be dir/** or file paths: {patterns}", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as file:
        changed = [path for path in file.read().split("\0") if path]
    code = [path for path in changed if is_code(path, patterns)]
    print(f"{len(code)} of {len(changed)} changed files are code", file=sys.stderr)
    print(f"code={'true' if changes_code(changed, patterns) else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
