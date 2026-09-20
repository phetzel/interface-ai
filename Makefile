SHELL := /bin/sh
.DEFAULT_GOAL := help

MODE ?= bank
SCENARIO ?= default
MEMBER_ID ?= 00123
CAPABILITY ?= manual-savings
PROMOTION_ID ?= discovered-savings
RUN ?=
export MODE SCENARIO MEMBER_ID RUN CAPABILITY PROMOTION_ID

# These commands share one desktop session, including when invoked with make -j.
.NOTPARALLEL:
.PHONY: help start audit-setup build up reset ready operator handoff-demo handoff-check logs stop down validate replay demo test check policy-check export replay-check fixture-install fixture-dev fixture-preview fixture-test build-check quick-check quality format discovery-probe discovery-check discover review promote m4-check

help: ## Show available commands (the default target)
	@awk 'BEGIN { FS = ":.*## "; print "Usage: make <target> [MODE=bank|native] [SCENARIO=default] [MEMBER_ID=00123]\n" } /^[a-zA-Z][a-zA-Z0-9_-]*:.*## / { printf "  %-18s %s\n", $$1, $$2 }' Makefile

start: build ## Build and launch a fresh bank demo; requires Docker and Make
	./scripts/desktop reset bank default
	./scripts/desktop validate-capability
	@echo 'Ready: open http://127.0.0.1:6081/ and choose Start lookup.'

audit-setup: fixture-install build ## Install audit tools, run quick checks, then launch a fresh bank desktop
	./apps/bank-fixture/node_modules/.bin/playwright install chromium
	$(MAKE) quick-check
	./scripts/desktop reset bank default
	./scripts/desktop validate-capability
	@echo 'Audit setup complete. Continue with the banking UI section of docs/manual-acceptance.html.'

build: ## Build both Docker images
	./scripts/desktop build
	./scripts/fixture build

up: ## Start the selected desktop and operator; MODE defaults to bank
	./scripts/desktop up "$$MODE" "$$SCENARIO"

reset: ## Recreate the selected desktop with a fresh session
	./scripts/desktop reset "$$MODE" "$$SCENARIO"

ready: ## Check desktop readiness and print session status
	./scripts/desktop ready

operator: ## Print the same-session operator panel URL
	./scripts/desktop operator

discover: ## Reset the synthetic bank and run bounded online goal discovery; host key + uv required
	./scripts/desktop reset bank default
	uv run --locked --script scripts/discover --member-id "$$MEMBER_ID"

discovery-probe: ## Test one real OpenAI-selected click on the current fresh bank desktop; host key + uv required
	uv run --locked --script scripts/discovery-probe

discovery-check: ## Test discovery transport with a simulated provider and real desktop; resets between cases
	python3 scripts/discovery-check

handoff-demo: ## Launch expiry; generated CAPABILITY starts its lookup and pauses for takeover
	./scripts/desktop reset bank expired
	@if [ "$$CAPABILITY" != manual-savings ]; then ./scripts/desktop replay --capability "$$CAPABILITY" --member-id "$$MEMBER_ID" --pause-for-human; fi
	@echo 'Open http://127.0.0.1:6081/; start a lookup if idle, then take control when paused.'

handoff-check: ## Run same-session acceptance with a simulated human operator
	./scripts/m3-check

logs: ## Show recent desktop and operator logs
	./scripts/desktop logs

stop: ## Stop further automation input; reset is required to resume
	./scripts/desktop stop-input

down: ## Stop project services; keep images and evidence
	./scripts/desktop down

validate: ## Validate the bundled capability and anchor assets
	./scripts/desktop validate-capability

replay: ## Replay MEMBER_ID on the current bank screen; no automatic reset
	./scripts/desktop replay --capability "$$CAPABILITY" --member-id "$$MEMBER_ID"

demo: ## Reset the bank scenario, then replay MEMBER_ID
	./scripts/desktop reset bank "$$SCENARIO"
	./scripts/desktop replay --capability "$$CAPABILITY" --member-id "$$MEMBER_ID"

test: ## Run the engine tests inside the running desktop
	./scripts/desktop test

check: ## Run full M1 acceptance; resets the synthetic desktop
	./scripts/m1-check

policy-check: ## Run M2 policy/evidence acceptance and the full M1 regression
	./scripts/m2-check

export: ## Export safe replay evidence; requires RUN=<replay-directory-name>
	@test -n "$$RUN" || { echo 'Usage: make export RUN=<replay-directory-name>' >&2; exit 2; }
	./scripts/desktop export-evidence --run "$$RUN"

replay-check: ## Run nine integration cases; ends on blocked loading
	./scripts/replay-check

fixture-install: ## Install the host React fixture dependencies (requires Node 22)
	npm --prefix apps/bank-fixture ci

fixture-dev: ## Start the host React development server
	npm --prefix apps/bank-fixture run dev

fixture-preview: ## Build and serve the host banking UI; run audit-setup or fixture-install first
	npm --prefix apps/bank-fixture run build
	npm --prefix apps/bank-fixture run preview

fixture-test: ## Build and run the fixture's Playwright tests on the host
	npm --prefix apps/bank-fixture test

build-check: ## Reject stale images and verify shipped engine/fixture bytes
	./scripts/build-check

quick-check: ## Run quality, unit, schema and type checks without a live desktop
	./scripts/quick-check

quality: ## Check active source formatting and Python correctness lint
	./scripts/quality

format: ## Format active source; never rewrites historical evidence
	./scripts/quality --write

review: ## Validate and evaluate a recorded candidate for member B and translated layout
	python3 scripts/review-capability review --run "$$RUN"

promote: ## Approve the exact evaluated candidate after reviewing its static crops and annotations
	python3 scripts/review-capability promote --run "$$RUN" --id "$$PROMOTION_ID"

m4-check: ## Check generated replay, same-session recovery, offline boundary and simulated provider rejection
	./scripts/m4-check
