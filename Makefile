SHELL := /bin/bash

DOCKER_DEFAULT_PLATFORM ?= linux/amd64

.EXPORT_ALL_VARIABLES:

.ONESHELL:

.phony:
	help

## ============================================================================
## Help Commands

help: ## Show help
	sed -ne '/sed/!s/## //p' $(MAKEFILE_LIST)

## ============================================================================
## docker Commands

go: ## All-in-one run container
	make rm \
	&& make build \
	&& make up \
	&& make log

build: ## build container image via docker
	$(call FUNC_MAKE_INIT) \
	&& docker build \
	--file Dockerfile \
	--tag ccip-app/ccip-server:latest \
	.

up: ## run container
	$(call FUNC_MAKE_INIT) \
	&& docker compose \
	up \
	--detach

log: ## get container log
	$(call FUNC_MAKE_INIT) \
	&& docker compose \
	logs \
	--follow \
	--tail 20

rm: ## rm container
	$(call FUNC_MAKE_INIT) \
	&& docker compose \
	rm \
	--stop \
	--force

shell: ## bash in container
	$(call FUNC_MAKE_INIT) \
	&& docker compose \
	exec \
	backend \
	bash

define FUNC_MAKE_INIT
	if [ -n "$$(command -v hr)" ]; then hr -; else echo "-----";fi \
	&& echo "⚙️ Running Makefile target: ${MAKECMDGOALS}"
endef
