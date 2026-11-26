from pathlib import Path

import pytest

from scripts.build_wiki import build, wiki_link_target

REF = "0123456789abcdef"
REPO_URL = "https://github.com/dono/repo"


@pytest.fixture
def wiki(tmp_path: Path) -> Path:
    out = tmp_path / "wiki"
    build(out, ref=REF, repo_url=REPO_URL)
    return out


@pytest.mark.parametrize(
    "markdown, expected",
    [
        ("[a](Arquitetura.md)", "[a](Arquitetura)"),
        ("[a](Home.md#topo)", "[a](Home#topo)"),
        ("[a](https://x.dev/README.md)", "[a](https://x.dev/README.md)"),
        ("[a](Home)", "[a](Home)"),
    ],
)
def test_should_drop_md_extension_when_link_is_relative(
    markdown: str, expected: str
) -> None:
    assert wiki_link_target(markdown) == expected


def test_should_write_guides_api_and_wiki_chrome_when_building(wiki: Path) -> None:
    pages = sorted(path.name for path in wiki.iterdir())

    assert pages == [
        "API-wiki_poc-money.md",
        "API-wiki_poc.md",
        "Arquitetura.md",
        "Home.md",
        "_Footer.md",
        "_Sidebar.md",
    ]


def test_should_list_home_first_when_building_sidebar(wiki: Path) -> None:
    sidebar = (wiki / "_Sidebar.md").read_text()

    assert sidebar.index("(Home)") < sidebar.index("(Arquitetura)")
    assert "- [wiki_poc.money](API-wiki_poc-money)" in sidebar


def test_should_render_signature_and_sections_when_function_has_docstring(
    wiki: Path,
) -> None:
    page = (wiki / "API-wiki_poc-money.md").read_text()

    assert "format_brl(cents: int, *, symbol: bool = True) -> str" in page
    assert "| `cents` | `int` | Valor em centavos. Aceita negativo. |" in page
    assert ">>> format_brl(123456)" in page
    assert "amounts() -> list[int]" in page
    assert f"{REPO_URL}/blob/{REF}/src/wiki_poc/money.py" in page


def test_should_skip_private_members_when_rendering_module(wiki: Path) -> None:
    page = (wiki / "API-wiki_poc-money.md").read_text()

    assert "_CENTS_PER_UNIT" not in page
    assert "__post_init__" not in page
