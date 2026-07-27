PY ?= venv/bin/python

.PHONY: setup test run-legacy run-v3 validate dashboard docs reports verify

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

verify:
	./scripts/verify.sh
