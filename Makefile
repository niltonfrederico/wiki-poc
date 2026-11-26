# Atalhos de desenvolvimento. `make` sem alvo lista todos.

.DEFAULT_GOAL := help
.PHONY: help setup lint test wiki clean

help: ## Lista os comandos disponíveis com descrição.
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}' | sort

setup: ## Instala as dependências (uv) e os hooks do pre-commit.
	uv sync
	uv run pre-commit install

lint: ## Ruff, pyright e demais hooks em todos os arquivos.
	uv run pre-commit run --all-files

test: ## Testes e doctests das docstrings.
	uv run pytest

wiki: ## Gera o wiki em build/wiki/, sem publicar.
	uv run python -m scripts.build_wiki --out build/wiki --ref "$$(git rev-parse HEAD 2>/dev/null || echo local)"

clean: ## Remove caches e build/.
	rm -rf .pytest_cache .ruff_cache build
