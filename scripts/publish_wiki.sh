#!/usr/bin/env bash
# Espelha a pasta gerada pelo build_wiki.py no repo do wiki (<repo>.wiki.git).
#
#   GH_TOKEN=... GITHUB_REPOSITORY=dono/repo scripts/publish_wiki.sh build/wiki
#
# Espelho com --delete: página que sai de docs/ (ou módulo removido) some do wiki.
# Edição feita direto no wiki é sobrescrita na próxima publicação.
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN ausente}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY ausente (dono/repo)}"
SRC="${1:-build/wiki}"
SHA="${GITHUB_SHA:-$(git rev-parse HEAD)}"
DEST="$(mktemp -d)"
trap 'rm -rf "$DEST"' EXIT

# Token no header, como o actions/checkout: fora da URL, do .git/config e do log.
AUTH="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"
git_auth() { git -c "http.https://github.com/.extraheader=$AUTH" "$@"; }

if ! git_auth clone --quiet --depth 1 \
    "https://github.com/${GITHUB_REPOSITORY}.wiki.git" "$DEST" 2>/dev/null; then
    # O GitHub só cria o <repo>.wiki.git quando a primeira página é salva pela UI.
    echo "::error::Wiki não inicializado. Crie qualquer página em" \
        "https://github.com/${GITHUB_REPOSITORY}/wiki e rode de novo."
    exit 1
fi

rsync -a --delete --exclude .git "$SRC/" "$DEST/"

cd "$DEST"
git add --all
if git diff --cached --quiet; then
    echo "Wiki já em dia com ${SHA::7}."
    exit 0
fi
git -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit --quiet -m "docs: sincroniza o wiki com ${SHA::7}"
git_auth push --quiet origin HEAD
echo "Wiki publicado: https://github.com/${GITHUB_REPOSITORY}/wiki"
