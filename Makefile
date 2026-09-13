SHELL := /bin/sh
.DEFAULT_GOAL := help

MODE ?= bank
SCENARIO ?= default
MEMBER_ID ?= 00123
export MODE SCENARIO MEMBER_ID

# These commands share one desktop session, including when invoked with make -j.
.NOTPARALLEL:
.PHONY: help build up reset ready viewer logs stop down validate replay demo test check replay-check fixture-install fixture-dev fixture-test

help: ## Show available commands (the default target)
	@awk 'BEGIN { FS = ":.*## "; print "Usage: make <target> [MODE=bank|native] [SCENARIO=default] [MEMBER_ID=00123]\n" } /^[a-zA-Z][a-zA-Z0-9_-]*:.*## / { printf "  %-18s %s\n", $$1, $$2 }' Makefile

build: ## Build both Docker images
	./scripts/desktop build
	./scripts/fixture build

up: ## Start the selected desktop and viewer; MODE defaults to bank
	./scripts/desktop up "$$MODE" "$$SCENARIO"

reset: ## Recreate the selected desktop with a fresh session
	./scripts/desktop reset "$$MODE" "$$SCENARIO"

ready: ## Check desktop readiness and print session status
	./scripts/desktop ready

viewer: ## Print the read-only viewer URL
	./scripts/desktop viewer

logs: ## Show recent desktop and viewer logs
	./scripts/desktop logs

stop: ## Stop further automation input; reset is required to resume
	./scripts/desktop stop-input

down: ## Stop project services; keep images and evidence
	./scripts/desktop down

validate: ## Validate the bundled capability and anchor assets
	./scripts/desktop validate-capability

replay: ## Replay MEMBER_ID on the current bank screen; no automatic reset
	./scripts/desktop replay --member-id "$$MEMBER_ID"

demo: ## Reset the bank scenario, then replay MEMBER_ID
	./scripts/desktop reset bank "$$SCENARIO"
	./scripts/desktop replay --member-id "$$MEMBER_ID"

test: ## Run the engine tests inside the running desktop
	./scripts/desktop test

check: ## Run full M1 acceptance; resets the synthetic desktop
	./scripts/m1-check

replay-check: ## Run nine integration cases; ends on blocked loading
	./scripts/replay-check

fixture-install: ## Install the host React fixture dependencies (requires Node 22)
	npm --prefix apps/bank-fixture ci

fixture-dev: ## Start the host React development server
	npm --prefix apps/bank-fixture run dev

fixture-test: ## Build and run the fixture's Playwright tests on the host
	npm --prefix apps/bank-fixture test
