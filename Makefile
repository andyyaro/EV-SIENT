.PHONY: help setup setup-core setup-gis run-v2 check-v2 full-v2 links docs-health health review clean-local status

PYTHON ?= python
PIP ?= pip

help:
	@echo "Future City Fellowship commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        Install core and GIS dependencies"
	@echo "  make setup-core   Install core dependencies only"
	@echo "  make setup-gis    Install GIS dependencies only"
	@echo ""
	@echo "Run/check:"
	@echo "  make run-v2       Run the full active V2 workflow"
	@echo "  make check-v2     Check V2 outputs and package sync"
	@echo "  make full-v2      Run V2 workflow, then check outputs"
	@echo "  make links        Check Markdown links with Lychee"
	@echo "  make docs-health  Alias for links"
	@echo "  make health       Run check-v2 and links"
	@echo "  make review       Run full-v2, links, and git status"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean-local  Remove local generated caches"
	@echo "  make status       Show git status"

setup: setup-core setup-gis

setup-core:
	$(PIP) install -r requirements.txt

setup-gis:
	$(PIP) install -r requirements-gis.txt

run-v2:
	$(PYTHON) src/run_v2.py

check-v2:
	$(PYTHON) src/check_outputs_v2.py

full-v2: run-v2 check-v2

links:
	lychee --verbose --no-progress \
	  --accept 200,204,206,301,302,303,307,308 \
	  --include-fragments \
	  --exclude-path data/outputs \
	  --exclude-path data/run_history \
	  './**/*.md'

docs-health: links

health: check-v2 links

review: full-v2 links status

clean-local:
	rm -rf data/source_extracts/gis/
	rm -rf data/run_history/
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

status:
	git status --short
