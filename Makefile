PY ?= venv/bin/python

.PHONY: setup test run-legacy run-v3 validate contract-v3 dashboard docs reports explorer explorer-legacy explorer-serve explorer-vendor nfc verify

setup:
	python3 -m venv venv && venv/bin/pip install -e ".[test]" -c requirements-lock.txt

test:
	$(PY) -m pytest tests/ -q --cov=fcf_m2 --cov-report=term

run-legacy:
	$(PY) -m fcf_m2.workflow run --mode legacy_v2 --out data/outputs/legacy_check

run-v3:
	$(PY) -m fcf_m2.workflow run --mode milestone2_v3 --out data/outputs/v3_run

# v3 is the authoritative contract (DEC-027); v1 and v2 are frozen history, still checked.
validate:
	$(PY) -m fcf_m2.workflow validate-contract data/contract/v3
	$(PY) -m fcf_m2.workflow validate-contract data/contract/v2
	$(PY) -m fcf_m2.workflow validate-contract data/contract/v1

contract-v3:
	$(PY) scripts/build_contract_v3.py

dashboard: run-v3
	$(PY) scripts/build_static_dashboard.py

docs:
	$(PY) -m fcf_m2.workflow docs

# Regenerates the DOCX deliverables from their Markdown sources. These had drifted:
# the tracked .docx carried a pre-reorganisation directory layout and a superseded
# port series that the Markdown no longer contained. Needs the [reports] extra
# (pip install -e ".[reports]"). The PDF is produced from the DOCX with LibreOffice,
# which is not a Python dependency -- skipped with a notice when soffice is absent.
reports:
	$(PY) scripts/md_to_docx.py reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx
	$(PY) scripts/md_to_docx.py reports/milestone-2/Milestone_2_Gap_Closure_Status.md reports/milestone-2/Milestone_2_Gap_Closure_Status.docx
	$(PY) scripts/md_to_docx.py docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md reports/milestone-2/FINAL_STANDARDS_APPLICATION_MATRIX.docx
	$(PY) scripts/md_to_docx.py docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md reports/milestone-2/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx
	@command -v soffice >/dev/null && soffice --headless --convert-to pdf --outdir reports/milestone-2 reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx || echo "soffice not found - DOCX regenerated, PDF left unchanged"

# --- 3D explorer -------------------------------------------------------------
# Projects the frozen model outputs into the viewer's payload. Defaults to the
# CANONICAL mode; the legacy target exists so the accepted V2 baseline stays
# reproducible, and it writes to a separate directory so the two can never be
# confused for one another.
explorer:
	$(PY) -m fcf3d.build_sites --repo . --mode milestone2_v3 --out explorer/web/data
	$(PY) -m fcf3d.build_models --sites explorer/web/data/sites.geojson --out explorer/web/models

explorer-legacy:
	$(PY) -m fcf3d.build_sites --repo . --mode legacy_v2 --out explorer/web/data-legacy_v2

## explorer-vendor - fetch CesiumJS locally so the viewer runs with no network
explorer-vendor:
	./scripts/vendor_cesium.sh

explorer-serve: explorer
	@echo "  3D explorer -> http://localhost:$(PORT)"
	@cd explorer/web && $(PY) -m http.server $(PORT)

PORT ?= 8080

## nfc - regenerate tag payloads, QR fallbacks, placement cards and landing pages
nfc:
	$(PY) scripts/build_nfc_tags.py
	$(PY) scripts/build_nfc_landing.py
	$(PY) scripts/build_capture_form.py

verify:
	./scripts/verify.sh

platform:
	$(PY) -m fcf_m2.launcher

platform-check:
	$(PY) -m fcf_m2.launcher --check
