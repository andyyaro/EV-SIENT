PY ?= venv/bin/python

.PHONY: setup test run-legacy run-v3 validate dashboard docs verify

setup:
	python3 -m venv venv && venv/bin/pip install -e ".[test]" -c requirements-lock.txt

test:
	$(PY) -m pytest tests/ -q --cov=fcf_m2 --cov-report=term

run-legacy:
	$(PY) -m fcf_m2.workflow run --mode legacy_v2 --out data/outputs/legacy_check

run-v3:
	$(PY) -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run

validate:
	$(PY) -m fcf_m2.workflow validate-contract data/contract/v1

dashboard: run-v3
	$(PY) scripts/build_static_dashboard.py

docs:
	$(PY) -m fcf_m2.workflow docs

verify:
	./scripts/verify.sh
