# Arquitetura

## Fluxo

1. Push na `main` que toca `docs/`, `src/` ou o gerador dispara o workflow `Wiki`.
2. `scripts/build_wiki.py` copia `docs/*.md` e gera uma página por módulo de `src/`, via [griffe](https://mkdocstrings.github.io/griffe/).
3. `scripts/publish_wiki.sh` clona o `<repo>.wiki.git`, espelha a pasta e dá push com o `GITHUB_TOKEN`.

Na PR, o CI só gera o wiki e anexa como artefato `wiki`: dá para ver o resultado antes do merge.

## Ajustes ao formato do wiki

| Wiki do GitHub | O gerador faz |
| --- | --- |
| Link entre páginas sem `.md` | Tira o `.md` dos links relativos de `docs/` |
| Ponto no nome lido como extensão | `wiki_poc.money` vira a página `API-wiki_poc-money` |
| Índice lateral é `_Sidebar.md` | Gera com guias e módulos |
| Sem pastas na navegação | Saída plana |

## Exemplos testados

Os `Examples:` das docstrings rodam como doctest no `pytest`. Exemplo quebrado falha o CI antes de chegar ao wiki.

Voltar para a [Home](Home.md#wiki-poc).
