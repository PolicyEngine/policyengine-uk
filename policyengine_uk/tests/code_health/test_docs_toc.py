"""The documentation site lists every page except the notebooks it leaves out on purpose, and its links reach pages.

The deploy workflow builds the site from myst.yml with ``myst build --html``,
and MyST makes a page only for a file the table of contents lists, by
``file:`` or by ``pattern:``. A page nothing lists never reaches the site, and
a link to a Markdown file or notebook the table of contents leaves out reaches
no page. The tests check that:

1. Every ``file:`` entry names a Markdown page or notebook in the repository,
   and no ``file:`` entry repeats another.
2. Every ``pattern:`` entry matches at least one page.
3. Every Markdown page and notebook under docs/book, and every notebook under
   docs, appears in the table of contents or in ``NOTEBOOKS_LEFT_OUT``.
4. Every relative link in a listed page, notebook Markdown cells included,
   reaches a listed page or an existing file, and its ``#`` anchor names a
   heading or label on the page it reaches. A bare ``#label`` link may name
   a ``(label)=`` target on any listed page, since MyST resolves those from
   every page. The links read are Markdown links
   and images, reference definitions, ``<a href>`` and ``<img src>`` tags,
   ``{doc}`` roles and the paths of ``{figure}`` and ``{image}`` directives.
   The test ignores links with a scheme (https:, mailto:) and anything inside
   fenced or inline code.
"""

import json
import re
from pathlib import Path
from urllib.parse import unquote

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
MYST_CONFIG = REPO_ROOT / "myst.yml"
if not MYST_CONFIG.is_file():
    # The release workflow tests the installed wheel, which has no docs.
    pytest.skip(
        "an installed package holds neither myst.yml nor the docs",
        allow_module_level=True,
    )

DOCS = REPO_ROOT / "docs"
DOCS_BOOK = DOCS / "book"
PAGE_SUFFIXES = {".md", ".ipynb"}
SKIPPED_FOLDERS = {"_build", ".ipynb_checkpoints"}

# Notebooks that myst.yml leaves out on purpose, each with its reason: the
# current parameters or the law contradict their stored outputs, or nobody can
# check them without survey data. They stay off the site until someone reruns
# them against the current model.
NOTEBOOKS_LEFT_OUT: dict[str, str] = {
    "docs/book/programs/gov/dcms/bbc/tv-licence.ipynb": (
        "Its fee table stops at the 2021 fee, and a cell hard-codes that fee "
        "as the current value."
    ),
    "docs/book/programs/gov/dwp/PIP.ipynb": (
        "Its enhanced mobility column shows the daily living standard rate, "
        "and its daily living table runs a year behind the parameters."
    ),
    "docs/book/programs/gov/dwp/universal-credit.ipynb": (
        "Each stored amount sits a year earlier than the parameters give it."
    ),
    "docs/book/programs/gov/hmrc/child-benefit.ipynb": (
        "Its 2022 table uses 2021 rates, and its code imports IndividualSim, "
        "which the package no longer has."
    ),
    "docs/book/programs/gov/hmrc/fuel-duty.ipynb": (
        "Its stored schedule differs from the parameters from 2027."
    ),
    "docs/book/programs/gov/hmrc/income-tax.ipynb": (
        "Its worked examples and dividend chart disagree with the model, and "
        "its allowance table reads each parameter's oldest value."
    ),
    "docs/book/programs/gov/hmrc/national-insurance.ipynb": (
        "Its employer rate for 6 April 2022 and its secondary threshold "
        "disagree with the parameters."
    ),
    "docs/book/programs/gov/ofgem/energy-price-guarantee.ipynb": (
        "Its price cap series predates the parameters' current figures."
    ),
    "docs/book/programs/gov/revenue_scotland/land-and-buildings-transaction-tax.ipynb": (
        "Its second-homes line uses the supplement before 5 December 2024."
    ),
    "docs/book/programs/gov/wra/land-transaction-tax.ipynb": (
        "Its chart shows main residential bands before 10 October 2022 and "
        "higher rates before 11 December 2024, and its code fails on a bracket "
        "whose latest threshold is null."
    ),
    "docs/book/validation/validation.ipynb": (
        "Its chart comes from an old run that needs survey data to check."
    ),
}

FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
# MyST directives that render their body as code.
CODE_DIRECTIVES = re.compile(r"^\{(code|code-block|code-cell|sourcecode|math)\}")
# MyST directives whose argument is a path to an image.
PATH_DIRECTIVE = re.compile(r"^\{(?:figure|image)\}\s+(?P<target>\S+)")
COLON_PATH_DIRECTIVE = re.compile(
    r"^ {0,3}:{3,}\{(?:figure|image)\}\s+(?P<target>\S+)", re.MULTILINE
)
INLINE_CODE = re.compile(r"(`+).+?\1")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_LINK = re.compile(r"\]\(\s*(?P<target><[^>]*>|[^\s)]+)(?:\s+[^)]*)?\)")
REFERENCE_DEFINITION = re.compile(
    r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(?P<target><[^>]*>|\S+)", re.MULTILINE
)
HTML_LINK = re.compile(
    r"<(?:a|img)\b[^>]*?\b(?:href|src)\s*=\s*(?:(?P<quote>[\"'])(?P<target>.*?)(?P=quote)|(?P<bare>[^\s\"'=<>`]+))",
    re.IGNORECASE,
)
DOC_ROLE = re.compile(r"\{doc\}`(?P<body>[^`]+)`")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(?P<text>.*?)\s*#*\s*$", re.MULTILINE)
LABEL = re.compile(r"^ {0,3}\((?P<label>[^()\s]+)\)=\s*$", re.MULTILINE)


def toc_entries(entries):
    """Yield every entry of a MyST table of contents, children included."""
    for entry in entries:
        yield entry
        yield from toc_entries(entry.get("children", []))


def read_toc(config_text: str) -> list[dict]:
    return list(toc_entries(yaml.safe_load(config_text)["project"]["toc"]))


def listed_pages(config_text: str) -> set[Path]:
    """The files a myst.yml table of contents publishes, by file or by pattern."""
    pages = set()
    for entry in read_toc(config_text):
        if "file" in entry:
            pages.add((REPO_ROOT / entry["file"]).resolve())
        if "pattern" in entry:
            pages.update(path.resolve() for path in REPO_ROOT.glob(entry["pattern"]))
    return pages


def pages_under(folder: Path, suffixes: set[str]) -> set[Path]:
    return {
        path.resolve()
        for path in folder.rglob("*")
        if path.suffix in suffixes
        and path.is_file()
        and not SKIPPED_FOLDERS & set(path.parts)
    }


def without_code(markdown: str, keep_inline_code: bool = False) -> str:
    """Drop fenced code, inline code and HTML comments from Markdown.

    A fence whose info string opens a MyST directive, such as ```{note}, keeps
    its body, since MyST renders that body as Markdown. A ``{figure}`` or
    ``{image}`` fence leaves its path behind as an image link.
    """
    kept = []
    open_fences = []  # (character, length, keeps its body)
    for line in markdown.splitlines():
        match = FENCE.match(line)
        if match:
            fence, info = match["fence"], match["info"].strip()
            innermost = open_fences[-1] if open_fences else None
            closes = (
                innermost is not None
                and not info
                and fence[0] == innermost[0]
                and len(fence) >= innermost[1]
            )
            if closes:
                open_fences.pop()
                continue
            if innermost is None or innermost[2]:
                keeps_body = info.startswith("{") and not CODE_DIRECTIVES.match(info)
                open_fences.append((fence[0], len(fence), keeps_body))
                directive = PATH_DIRECTIVE.match(info)
                if directive:
                    kept.append(f"![]({directive['target']})")
                continue
        if all(keeps_body for _, _, keeps_body in open_fences):
            kept.append(line)
    text = HTML_COMMENT.sub("", "\n".join(kept))
    return text if keep_inline_code else INLINE_CODE.sub("", text)


def page_markdown(page: Path) -> str:
    if page.suffix == ".ipynb":
        cells = json.loads(page.read_text(encoding="utf-8"))["cells"]
        return "\n\n".join(
            "".join(cell["source"])
            if isinstance(cell["source"], list)
            else cell["source"]
            for cell in cells
            if cell["cell_type"] == "markdown"
        )
    return page.read_text(encoding="utf-8")


def relative_links(markdown: str) -> list[str]:
    """Targets of the links and images that point into the repository."""
    with_roles = without_code(markdown, keep_inline_code=True)
    text = INLINE_CODE.sub("", with_roles)
    targets = [m["target"] for m in INLINE_LINK.finditer(text)]
    targets += [m["target"] for m in REFERENCE_DEFINITION.finditer(text)]
    targets += [m["target"] or m["bare"] for m in HTML_LINK.finditer(text)]
    targets += [m["target"] for m in COLON_PATH_DIRECTIVE.finditer(text)]
    for match in DOC_ROLE.finditer(with_roles):
        body = match["body"].strip()
        explicit = re.search(r"<(?P<target>[^<>]+)>\s*$", body)
        targets.append(explicit["target"] if explicit else body)
    relative = []
    for target in targets:
        target = target.strip("<>").strip()
        if not target or target.startswith("//") or SCHEME.match(target):
            continue
        relative.append(target)
    return relative


def slug(heading: str) -> str:
    """The anchor MyST gives a heading.

    MyST drops quotation marks, lower-cases the text, turns every other
    character outside a-z, 0-9 and the hyphen into a hyphen, prefixes "id-"
    when the result starts with a digit or hyphen, and collapses runs of
    hyphens.
    """
    text = re.sub(r"['‘’\"“”]+", "", " ".join(heading.split())).lower()
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"^([0-9-])", r"id-\1", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def labels(page: Path) -> frozenset[str]:
    """The ``(label)=`` targets a page defines."""
    text = without_code(page_markdown(page), keep_inline_code=True)
    return frozenset(m["label"] for m in LABEL.finditer(text))


def anchors(page: Path) -> frozenset[str]:
    """The heading anchors and ``(label)=`` targets a page defines."""
    text = without_code(page_markdown(page), keep_inline_code=True)
    found = {slug(m["text"].replace("`", "")) for m in HEADING.finditer(text)}
    return frozenset(found) | labels(page)


def defines_label(label: str, pages: set[Path]) -> bool:
    """Whether a listed page defines a ``(label)=`` target. MyST resolves
    such a label from every page."""
    return any(
        label in labels(page)
        for page in pages
        if page.suffix in PAGE_SUFFIXES and page.is_file()
    )


def link_problem(page: Path, target: str, pages: set[Path]) -> str | None:
    """Why a relative link from a page misses, or None when it reaches a page."""
    path, _, anchor = unquote(target.split("?", 1)[0]).partition("#")
    if not path:
        resolved = page.resolve()
    else:
        base = REPO_ROOT if path.startswith("/") else page.parent
        resolved = (base / path.lstrip("/")).resolve()
    if resolved not in pages and resolved.suffix not in PAGE_SUFFIXES:
        if resolved.is_dir():
            return "names a folder, which has no page on the site"
        if resolved.is_file():
            return None
        resolved = next(
            (
                resolved.with_suffix(suffix)
                for suffix in sorted(PAGE_SUFFIXES)
                if resolved.with_suffix(suffix) in pages
            ),
            resolved,
        )
    if resolved not in pages:
        if resolved.suffix in PAGE_SUFFIXES and resolved.is_file():
            return "names a page myst.yml does not list"
        return "names no file"
    if anchor and anchor not in anchors(resolved):
        # MyST resolves a bare #anchor from any page, but warns when it
        # names a heading there; the test accepts only an explicit label.
        if not path and defines_label(anchor, pages):
            return None
        return f"names no heading or label #{anchor} on its page"
    return None


def broken_links(pages: set[Path]) -> list[str]:
    problems = []
    for page in sorted(pages):
        if page.suffix not in PAGE_SUFFIXES or not page.is_file():
            continue
        for target in relative_links(page_markdown(page)):
            problem = link_problem(page, target, pages)
            if problem:
                where = page.relative_to(REPO_ROOT)
                problems.append(f"{where}: ({target}) {problem}")
    return problems


TOC = read_toc(MYST_CONFIG.read_text(encoding="utf-8"))
PAGES = listed_pages(MYST_CONFIG.read_text(encoding="utf-8"))


def test_every_file_entry_names_a_page():
    files = [entry["file"] for entry in TOC if "file" in entry]
    missing = [
        file
        for file in files
        if Path(file).suffix not in PAGE_SUFFIXES or not (REPO_ROOT / file).is_file()
    ]
    assert missing == []
    resolved = [(REPO_ROOT / file).resolve() for file in files]
    repeated = sorted(
        {file for file, path in zip(files, resolved) if resolved.count(path) > 1}
    )
    assert repeated == []


def test_every_pattern_matches_a_page():
    empty = [
        entry["pattern"]
        for entry in TOC
        if "pattern" in entry
        and not any(
            path.suffix in PAGE_SUFFIXES for path in REPO_ROOT.glob(entry["pattern"])
        )
    ]
    assert empty == []


def test_every_notebook_in_docs_is_in_the_table_of_contents():
    notebooks = pages_under(DOCS, {".ipynb"})
    left_out = {(REPO_ROOT / path).resolve() for path in NOTEBOOKS_LEFT_OUT}
    unlisted = notebooks - PAGES - left_out
    assert sorted(str(path.relative_to(REPO_ROOT)) for path in unlisted) == []
    # An exclusion must name a notebook that exists and that myst.yml omits.
    stale = {path for path in left_out if path not in notebooks or path in PAGES}
    assert sorted(str(path.relative_to(REPO_ROOT)) for path in stale) == []
    unexplained = [
        path for path, reason in NOTEBOOKS_LEFT_OUT.items() if not reason.strip()
    ]
    assert unexplained == []


def test_every_markdown_page_in_docs_book_is_in_the_table_of_contents():
    unlisted = pages_under(DOCS_BOOK, {".md"}) - PAGES
    assert sorted(str(path.relative_to(REPO_ROOT)) for path in unlisted) == []


def test_every_relative_link_in_a_listed_page_reaches_a_page_or_file():
    assert broken_links(PAGES) == []


@pytest.mark.parametrize(
    "markdown, expected",
    [
        ("See [the page](other.md).", ["other.md"]),
        ("![chart](images/chart.png)", ["images/chart.png"]),
        ('[titled](page.md "Title")', ["page.md"]),
        ("[angled](<a page.md>)", ["a page.md"]),
        ("[ref]: ../validation/\n", ["../validation/"]),
        ("[web](https://example.com) [mail](mailto:a@b.c)", []),
        ("[anchor](#section)", ["#section"]),
        ("Use `[x](not-a-link.md)` here.", []),
        ("```python\n# [x](code.md)\n```\n", []),
        ("~~~\n[x](code.md)\n~~~\n", []),
        ("```{note}\nSee [x](note.md).\n```\n", ["note.md"]),
        ("```{code-cell}\n[x](cell.md)\n```\n", []),
        ("````{tip}\n```python\n[x](code.md)\n```\n[y](tip.md)\n````\n", ["tip.md"]),
        ("<!-- [x](comment.md) -->", []),
        ("[^1]: A footnote, not a link.\n", []),
        ("<a href=\"page.md\">x</a> <img src='chart.png'>", ["page.md", "chart.png"]),
        ('<a href="https://example.com">x</a>', []),
        ("See {doc}`../index` and {doc}`the guide <guide>`.", ["../index", "guide"]),
        ("```{figure} images/chart.png\nA caption.\n```\n", ["images/chart.png"]),
        (":::{image} logo.png\n:::\n", ["logo.png"]),
        ("```python\n{doc}`code`\n```\n", []),
    ],
)
def test_relative_links_reads_only_links_outside_code(markdown, expected):
    assert relative_links(markdown) == expected


def test_link_problem_tells_a_listed_page_from_an_unlisted_one():
    page = DOCS_BOOK / "usage" / "scenarios.md"
    listed = {page.resolve(), (DOCS_BOOK / "index.md").resolve()}
    assert link_problem(page, "../index.md", listed) is None
    assert link_problem(page, "../index", listed) is None
    assert link_problem(page, "../%69ndex.md", listed) is None
    assert link_problem(page, "../logo.png", listed) is None
    assert "does not list" in link_problem(page, "simulations.md", listed)
    assert "folder" in link_problem(page, "../validation/", listed)
    assert link_problem(page, "missing.md", listed) == "names no file"


def test_link_problem_checks_the_anchor_on_the_page_it_reaches():
    page = DOCS_BOOK / "usage" / "scenarios.md"
    listed = {page.resolve(), (DOCS_BOOK / "index.md").resolve()}
    assert link_problem(page, "#your-first-policy-scenario", listed) is None
    assert link_problem(page, "scenarios.md#your-first-policy-scenario", listed) is None
    assert "#no-such-heading" in link_problem(page, "#no-such-heading", listed)
    assert "#top" in link_problem(page, "../index.md#top", listed)


def test_a_bare_label_link_reaches_a_label_on_another_listed_page(tmp_path):
    labelled = tmp_path / "labelled.md"
    labelled.write_text("(sp-label)=\n## State Pension\n\n## Elsewhere\n")
    linking = tmp_path / "linking.md"
    linking.write_text("See [the State Pension](#sp-label).\n")
    listed = {labelled.resolve(), linking.resolve()}
    assert link_problem(linking, "#sp-label", listed) is None
    assert "#no-such-label" in link_problem(linking, "#no-such-label", listed)
    # The test rejects a bare link to a heading on another page.
    assert "#elsewhere" in link_problem(linking, "#elsewhere", listed)
    # A label on a page myst.yml does not list resolves nowhere.
    assert "#sp-label" in link_problem(linking, "#sp-label", {linking.resolve()})


@pytest.mark.parametrize(
    "heading, expected",
    [
        ("Your first policy scenario", "your-first-policy-scenario"),
        ("Energy Price Guarantee (EPG)", "energy-price-guarantee-epg"),
        ("2024–25 rates", "id-2024-25-rates"),
        ("Who’s eligible", "whos-eligible"),
    ],
)
def test_slug_joins_the_words_of_a_heading_with_hyphens(heading, expected):
    assert slug(heading) == expected
