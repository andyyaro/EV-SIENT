.PHONY: help setup setup-core setup-gis run-v2 check-v2 tableau-exports check-tableau full-v2 full-v2-tableau links health review clean-local status

PYTHON ?= python
PIP ?= pip

help:
	@echo "Future City Fellowship commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup             Install core and GIS dependencies"
	@echo "  make setup-core        Install core dependencies only"
	@echo "  make setup-gis         Install GIS dependencies only"
	@echo ""
	@echo "Run/check:"
	@echo "  make run-v2            Run the full active V2 workflow"
	@echo "  make check-v2          Check V2 outputs and package sync"
	@echo "  make tableau-exports   Clean and regenerate Tableau CSV inputs from V2 outputs"
	@echo "  make check-tableau     Validate Tableau export files, schemas, row counts, and site coverage"
	@echo "  make full-v2           Run V2 workflow, then check outputs"
	@echo "  make full-v2-tableau   Run/check V2, then regenerate and check Tableau CSV inputs"
	@echo "  make links             Check Markdown links with Lychee"
	@echo "  make health            Run check-v2, check-tableau, and links"
	@echo "  make review            Run full-v2-tableau, links, and git status"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean-local       Remove local generated caches"
	@echo "  make status            Show git status"

setup: setup-core setup-gis

setup-core:
	$(PIP) install -r requirements.txt

setup-gis:
	$(PIP) install -r requirements-gis.txt

run-v2:
	$(PYTHON) src/run_v2.py

check-v2:
	$(PYTHON) src/check_outputs_v2.py

tableau-exports:
	mkdir -p data/outputs/tableau
	rm -f data/outputs/tableau/tableau_*.csv
	$(PYTHON) src/build_tableau_exports.py

check-tableau:
	$(PYTHON) src/check_tableau_exports.py

full-v2: run-v2 check-v2

full-v2-tableau: full-v2 tableau-exports check-tableau

links:
	lychee --verbose --no-progress \
	  --accept 200,204,206,301,302,303,307,308 \
	  --include-fragments \
	  --exclude-path data/outputs \
	  --exclude-path data/run_history \
	  './**/*.md'

health: check-v2 check-tableau links

review: full-v2-tableau links status

clean-local:
	rm -rf data/source_extracts/gis/
	rm -rf data/run_history/
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

status:
	git status --short
