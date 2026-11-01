"""The documentation site publishes every notebook, and its links reach pages.

The deploy workflow builds the site from myst.yml with ``myst build --html``,
and MyST makes a page only for a file the table of contents lists, by
``file:`` or by ``pattern:``. A notebook nothing lists never reaches the site,
and a link to a Markdown file or notebook the table of contents leaves out
reaches no page. These tests hold the docs to that:

1. Every ``file:`` entry names a file in the repository.
2. Every notebook under docs/book appears in the table of contents.
3. Every relative Markdown link in a listed page, notebook Markdown cells
   included, reaches a listed page or an existing file. The test ignores links
   with a scheme (https:, mailto:), bare ``#`` anchors, and anything inside
   fenced or inline code.
"""

import json
import re
from pathlib import Path

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

DOCS_BOOK = REPO_ROOT / "docs" / "book"
PAGE_SUFFIXES = {".md", ".ipynb"}

# Notebooks under docs/book that myst.yml leaves out on purpose, each with its
# reason, such as a stored error or a local path in its outputs.
NOTEBOOKS_LEFT_OUT: dict[str, str] = {}

FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
# MyST directives whose body is code rather than Markdown.
CODE_DIRECTIVES = re.compile(r"^\{(code|code-block|code-cell|sourcecode|math)\}")
INLINE_CODE = re.compile(r"(`+).+?\1")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_LINK = re.compile(r"\]\(\s*(?P<target><[^>]*>|[^\s)]+)(?:\s+[^)]*)?\)")
REFERENCE_DEFINITION = re.compile(
    r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(?P<target><[^>]*>|\S+)", re.MULTILINE
)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def toc_entries(entries):
    """Yield every entry of a MyST table of contents, children included."""
    for entry in entries:
        yield entry
        yield from toc_entries(entry.get("children", []))


def listed_pages(config_text: str) -> set[Path]:
    """The files a myst.yml table of contents publishes, by file or by pattern."""
    toc = yaml.safe_load(config_text)["project"]["toc"]
    pages = set()
    for entry in toc_entries(toc):
        if "file" in entry:
            pages.add((REPO_ROOT / entry["file"]).resolve())
        if "pattern" in entry:
            pages.update(path.resolve() for path in REPO_ROOT.glob(entry["pattern"]))
    return pages


def without_code(markdown: str) -> str:
    """Drop fenced code, inline code and HTML comments from Markdown.

    A fence whose info string opens a MyST directive, such as ```{note}, keeps
    its body, since MyST renders that body as Markdown.
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
                continue
        if all(keeps_body for _, _, keeps_body in open_fences):
            kept.append(line)
    text = HTML_COMMENT.sub("", "\n".join(kept))
    return INLINE_CODE.sub("", text)


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
    """Targets of the Markdown links and images that point into the repository."""
    text = without_code(markdown)
    targets = [m["target"] for m in INLINE_LINK.finditer(text)]
    targets += [m["target"] for m in REFERENCE_DEFINITION.finditer(text)]
    relative = []
    for target in targets:
        target = target.strip("<>")
        if not target or target.startswith(("#", "//")) or SCHEME.match(target):
            continue
        relative.append(target)
    return relative


def link_problem(page: Path, target: str, pages: set[Path]) -> str | None:
    """Why a relative link from a page misses, or None when it reaches a page."""
    path = re.split(r"[#?]", target, maxsplit=1)[0]
    base = REPO_ROOT if path.startswith("/") else page.parent
    resolved = (base / path.lstrip("/")).resolve()
    if resolved in pages:
        return None
    if resolved.suffix in PAGE_SUFFIXES:
        if resolved.is_file():
            return "names a page myst.yml does not list"
        return "names no file"
    if resolved.is_dir():
        return "is a folder, which the site has no page for"
    if resolved.is_file():
        return None
    if any(resolved.with_suffix(suffix) in pages for suffix in PAGE_SUFFIXES):
        return None
    return "names no file"


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


PAGES = listed_pages(MYST_CONFIG.read_text(encoding="utf-8"))


def test_every_file_entry_names_a_file():
    toc = yaml.safe_load(MYST_CONFIG.read_text(encoding="utf-8"))["project"]["toc"]
    missing = [
        entry["file"]
        for entry in toc_entries(toc)
        if "file" in entry and not (REPO_ROOT / entry["file"]).is_file()
    ]
    assert missing == []


def test_every_notebook_in_docs_book_is_in_the_table_of_contents():
    notebooks = {
        path.resolve()
        for path in DOCS_BOOK.rglob("*.ipynb")
        if not {"_build", ".ipynb_checkpoints"} & set(path.parts)
    }
    left_out = {(REPO_ROOT / path).resolve() for path in NOTEBOOKS_LEFT_OUT}
    unlisted = notebooks - PAGES - left_out
    assert sorted(str(path.relative_to(REPO_ROOT)) for path in unlisted) == []
    # An exclusion must name a notebook that exists and that myst.yml omits.
    stale = {path for path in left_out if path not in notebooks or path in PAGES}
    assert sorted(str(path.relative_to(REPO_ROOT)) for path in stale) == []


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
        ("[anchor](#section)", []),
        ("Use `[x](not-a-link.md)` here.", []),
        ("```python\n# [x](code.md)\n```\n", []),
        ("~~~\n[x](code.md)\n~~~\n", []),
        ("```{note}\nSee [x](note.md).\n```\n", ["note.md"]),
        ("```{code-cell}\n[x](cell.md)\n```\n", []),
        ("````{tip}\n```python\n[x](code.md)\n```\n[y](tip.md)\n````\n", ["tip.md"]),
        ("<!-- [x](comment.md) -->", []),
        ("[^1]: A footnote, not a link.\n", []),
    ],
)
def test_relative_links_reads_only_links_outside_code(markdown, expected):
    assert relative_links(markdown) == expected


def test_link_problem_tells_a_listed_page_from_an_unlisted_one():
    page = DOCS_BOOK / "usage" / "scenarios.md"
    listed = {page.resolve(), (DOCS_BOOK / "index.md").resolve()}
    assert link_problem(page, "../index.md#top", listed) is None
    assert link_problem(page, "../index", listed) is None
    assert link_problem(page, "../logo.png", listed) is None
    assert "does not list" in link_problem(page, "simulations.md", listed)
    assert "folder" in link_problem(page, "../validation/", listed)
    assert link_problem(page, "missing.md", listed) == "names no file"
