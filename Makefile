SHELL := /bin/sh
.DEFAULT_GOAL := help

MODE ?= bank
SCENARIO ?= default
MEMBER_ID ?= 00123
CAPABILITY ?= discovered-savings
PROMOTION_ID ?= discovered-savings
SUITE ?= quick
RUN ?=
GOAL ?=
TARGET ?= synthetic-bank
export MODE SCENARIO MEMBER_ID RUN CAPABILITY PROMOTION_ID GOAL TARGET SUITE

# These commands share one desktop session, including when invoked with make -j.
.NOTPARALLEL:

help: ## Show the assessment commands
	@awk 'BEGIN { FS = ":.*## "; print "Usage: make <command> [NAME=value]\n" } /^[a-zA-Z][a-zA-Z0-9_-]*:.*## / { printf "  %-14s %s\n", $$1, $$2 }' Makefile
	@echo 'Checks: SUITE=quick|full|desktop|policy|replay|handoff|discovery|operator|generated'
	@echo 'Development commands: make help-dev'

help-dev:
	@echo 'build, start, up, reset, ready, operator, logs, stop, validate, replay, demo, export'
	@echo 'fixture-install, fixture-dev, fixture-preview, fixture-test, build-check, quality, format, dev-setup'

start: build
	./scripts/desktop reset bank default
	./scripts/desktop validate-capability --capability "$$CAPABILITY"
	@echo 'Ready: open http://127.0.0.1:6081/ and choose Start lookup.'

assess: build ## Build and demonstrate the generated capability for member B; no key required
	$(MAKE) demo MEMBER_ID=00456

dev-setup: fixture-install build
	./apps/bank-fixture/node_modules/.bin/playwright install chromium
	$(MAKE) check SUITE=quick
	./scripts/desktop reset bank default
	./scripts/desktop validate-capability --capability "$$CAPABILITY"
	@echo 'Development setup complete. See docs/DEMO.md for the walkthrough.'

build:
	./scripts/desktop build
	./scripts/fixture build

up:
	./scripts/desktop up "$$MODE" "$$SCENARIO"

reset:
	./scripts/desktop reset "$$MODE" "$$SCENARIO"

ready:
	./scripts/desktop ready

operator:
	./scripts/desktop operator

discover: ## Reset the synthetic bank and run bounded online goal discovery; host key + uv required
	uv run --locked --script scripts/discover --reset $(if $(filter command line environment,$(origin MEMBER_ID)),--member-id "$$MEMBER_ID",) --goal "$$GOAL" --target "$$TARGET"


handoff: ## Reset and pause the generated workflow for same-session takeover
	./scripts/desktop reset bank expired
	@if [ "$$CAPABILITY" != manual-savings ]; then ./scripts/desktop replay --capability "$$CAPABILITY" --member-id "$$MEMBER_ID" --pause-for-human; fi
	@echo 'Open http://127.0.0.1:6081/; start a lookup if idle, then take control when paused.'


logs:
	./scripts/desktop logs

stop:
	./scripts/desktop stop-input

down: ## Stop project services; keep images and evidence
	./scripts/desktop down

validate:
	./scripts/desktop validate-capability --capability "$$CAPABILITY"

replay:
	./scripts/desktop replay --capability "$$CAPABILITY" --member-id "$$MEMBER_ID"

demo:
	./scripts/desktop reset bank "$$SCENARIO"
	./scripts/desktop replay --capability "$$CAPABILITY" --member-id "$$MEMBER_ID"

check: ## Run automated checks (SUITE=quick by default; full includes live tests)
	./scripts/check --suite "$$SUITE"

export:
	@test -n "$$RUN" || { echo 'Usage: make export RUN=<replay-directory-name>' >&2; exit 2; }
	./scripts/desktop export-evidence --run "$$RUN"


fixture-install:
	npm --prefix apps/bank-fixture ci

fixture-dev:
	npm --prefix apps/bank-fixture run dev

fixture-preview:
	npm --prefix apps/bank-fixture run build
	npm --prefix apps/bank-fixture run preview

fixture-test:
	npm --prefix apps/bank-fixture test

build-check:
	./scripts/build-check


quality:
	./scripts/quality

format:
	./scripts/quality --write

review: ## Validate and evaluate a recorded candidate for member B and translated layout
	python3 scripts/review-capability review --run "$$RUN"

promote: ## Approve the exact evaluated candidate after reviewing its static crops and annotations
	python3 scripts/review-capability promote --run "$$RUN" --id "$$PROMOTION_ID"

# Transitional aliases; new documentation uses check/handoff.
quick-check:
	$(MAKE) check SUITE=quick
handoff-demo: handoff

.PHONY: help help-dev start assess dev-setup build up reset ready operator discover handoff logs stop down validate replay demo check export fixture-install fixture-dev fixture-preview fixture-test build-check quality format review promote quick-check handoff-demo
