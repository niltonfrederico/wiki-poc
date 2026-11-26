"""Monta o wiki do repo: as páginas de `docs/` e a referência de API das docstrings.

Saída plana em `--out`, no formato do GitHub Wiki: link entre páginas sem `.md`,
índice lateral em `_Sidebar.md` e rodapé em `_Footer.md`. O `publish_wiki.sh`
espelha essa pasta no `<repo>.wiki.git`.

    uv run python -m scripts.build_wiki --out build/wiki --ref "$(git rev-parse HEAD)"
"""

import argparse
import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import griffe

PACKAGE: Final = "wiki_poc"
SRC_DIR: Final = Path("src")
DOCS_DIR: Final = Path("docs")
API_PREFIX: Final = "API-"
HOME: Final = "Home"

# Link relativo para `.md` (com âncora opcional). URL absoluta fica como está.
_MD_LINK_RE: Final = re.compile(r"\]\((?![a-z]+://)([^)#\s]+)\.md(#[^)\s]*)?\)")


def wiki_link_target(markdown: str) -> str:
    """Tira o `.md` dos links relativos: no wiki, a página é endereçada sem ele."""
    return _MD_LINK_RE.sub(r"](\1\2)", markdown)


def api_page_name(module: griffe.Module) -> str:
    """Nome da página de um módulo. Hífen no lugar do ponto: o wiki lê o ponto
    como início da extensão do arquivo."""
    return API_PREFIX + module.path.replace(".", "-")


def iter_modules(module: griffe.Module) -> Iterator[griffe.Module]:
    yield module
    for submodule in sorted(module.modules.values(), key=lambda m: m.path):
        if submodule.is_public:
            yield from iter_modules(submodule)


def _public_members[T: griffe.Object](parent: griffe.Object, kind: type[T]) -> list[T]:
    members = [
        member
        for name, member in parent.members.items()
        if isinstance(member, kind) and not name.startswith("_")
    ]
    return sorted(members, key=lambda m: m.lineno or 0)


def _signature(function: griffe.Function) -> str:
    parts: list[str] = []
    keyword_marker_done = False
    for parameter in function.parameters:
        if parameter.name in {"self", "cls"}:
            continue
        name = parameter.name
        match parameter.kind:
            case griffe.ParameterKind.var_positional:
                name = f"*{name}"
                keyword_marker_done = True
            case griffe.ParameterKind.var_keyword:
                name = f"**{name}"
            case griffe.ParameterKind.keyword_only if not keyword_marker_done:
                parts.append("*")
                keyword_marker_done = True
            case _:
                pass
        if parameter.annotation is not None:
            name += f": {parameter.annotation}"
        if parameter.default is not None:
            name += f" = {parameter.default}"
        parts.append(name)
    returns = f" -> {function.returns}" if function.returns is not None else ""
    return f"{function.name}({', '.join(parts)}){returns}"


def _render_section(section: griffe.DocstringSection) -> list[str]:
    match section:
        case griffe.DocstringSectionText():
            return [section.value, ""]
        case griffe.DocstringSectionParameters() | griffe.DocstringSectionAttributes():
            title = (
                "Parâmetros"
                if isinstance(section, griffe.DocstringSectionParameters)
                else "Atributos"
            )
            rows = [
                f"| `{item.name}` | `{item.annotation or ''}` | {item.description} |"
                for item in section.value
            ]
            header = [
                f"**{title}**",
                "",
                "| Nome | Tipo | Descrição |",
                "|---|---|---|",
            ]
            return [*header, *rows, ""]
        case griffe.DocstringSectionReturns():
            items = [
                f"- `{item.annotation}`: {item.description}" for item in section.value
            ]
            return ["**Retorna**", "", *items, ""]
        case griffe.DocstringSectionRaises():
            items = [
                f"- `{item.annotation}`: {item.description}" for item in section.value
            ]
            return ["**Levanta**", "", *items, ""]
        case griffe.DocstringSectionExamples():
            lines = ["**Exemplos**", ""]
            for kind, text in section.value:
                if kind is griffe.DocstringSectionKind.examples:
                    lines += ["```python", text, "```", ""]
                else:
                    lines += [text, ""]
            return lines
        case griffe.DocstringSectionAdmonition():
            body = section.value.description.replace("\n", "\n> ")
            return [f"> **{section.title}:** {body}", ""]
        case _:
            return []


def _render_docstring(obj: griffe.Object) -> list[str]:
    if obj.docstring is None:
        return []
    return [line for s in obj.docstring.parsed for line in _render_section(s)]


def _render_function(function: griffe.Function, heading: str) -> list[str]:
    return [
        f"{heading} `{function.name}`",
        "",
        "```python",
        _signature(function),
        "```",
        "",
        *_render_docstring(function),
    ]


def render_module(module: griffe.Module, source_url: str) -> str:
    """Página de um módulo: docstring dele, depois classes e funções públicas."""
    lines = [f"# `{module.path}`", "", *_render_docstring(module)]
    relative = module.relative_filepath.as_posix()
    lines += [f"Fonte: [`{relative}`]({source_url}/{relative})", ""]

    for cls in _public_members(module, griffe.Class):
        lines += [f"## `{cls.name}`", "", *_render_docstring(cls)]
        for method in _public_members(cls, griffe.Function):
            lines += _render_function(method, "###")

    for function in _public_members(module, griffe.Function):
        lines += _render_function(function, "##")

    return "\n".join(lines).rstrip() + "\n"


def _sidebar(guides: list[str], api_pages: list[str]) -> str:
    lines = ["**Guias**", "", *(f"- [{g.replace('-', ' ')}]({g})" for g in guides)]
    lines += ["", "**API**", ""]
    lines += [
        f"- [{page.removeprefix(API_PREFIX).replace('-', '.')}]({page})"
        for page in api_pages
    ]
    return "\n".join(lines) + "\n"


def build(out: Path, *, ref: str, repo_url: str) -> list[str]:
    """Gera o wiki em `out`, apagando o que havia lá. Devolve as páginas criadas.

    Args:
        out: Pasta de saída. É recriada do zero a cada execução.
        ref: Commit de origem, citado no rodapé e nos links para a fonte.
        repo_url: URL do repo no GitHub, base dos links para a fonte.

    Returns:
        Nomes das páginas (sem `.md`), na ordem do índice lateral.
    """
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    guide_files = sorted(DOCS_DIR.glob("*.md"), key=lambda p: (p.stem != HOME, p.stem))
    guides = [path.stem for path in guide_files]
    for path in guide_files:
        (out / path.name).write_text(wiki_link_target(path.read_text()))

    package = griffe.load(PACKAGE, search_paths=[SRC_DIR], docstring_parser="google")
    if not isinstance(package, griffe.Module):
        raise TypeError(f"{PACKAGE} não é um módulo")
    # `relative_filepath` já começa em `src/`.
    source_url = f"{repo_url}/blob/{ref}"
    api_pages: list[str] = []
    for module in iter_modules(package):
        page = api_page_name(module)
        (out / f"{page}.md").write_text(render_module(module, source_url))
        api_pages.append(page)

    (out / "_Sidebar.md").write_text(_sidebar(guides, api_pages))
    (out / "_Footer.md").write_text(
        f"Gerado de [`{ref[:7]}`]({repo_url}/commit/{ref}). Não edite aqui: "
        "a próxima publicação sobrescreve. A fonte é `docs/` e as docstrings.\n"
    )
    return guides + api_pages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monta o wiki do repo a partir de docs/ e das docstrings."
    )
    parser.add_argument("--out", type=Path, default=Path("build/wiki"))
    parser.add_argument("--ref", required=True, help="SHA do commit de origem")
    parser.add_argument(
        "--repo-url", default="https://github.com/niltonfrederico/wiki-poc"
    )
    args = parser.parse_args()
    out: Path = args.out
    ref: str = args.ref
    repo_url: str = args.repo_url
    pages = build(out, ref=ref, repo_url=repo_url)
    print(f"{len(pages)} páginas em {out}: {', '.join(pages)}")  # noqa: T201


if __name__ == "__main__":
    main()
