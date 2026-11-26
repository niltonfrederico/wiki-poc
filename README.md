# wiki-poc

POC: o GitHub Wiki deste repo é publicado sozinho a partir de `docs/` e das
docstrings de `src/`. Detalhes em [docs/Arquitetura.md](docs/Arquitetura.md).

## Uso

```bash
make setup   # uv sync + hooks
make test    # pytest + doctests
make wiki    # gera build/wiki/ sem publicar
```

Publicação: workflow `Wiki`, a cada push na `main`.

## Primeira vez

O GitHub só cria o `<repo>.wiki.git` depois da primeira página salva pela UI.
Crie qualquer página em `/wiki` antes do primeiro push.
