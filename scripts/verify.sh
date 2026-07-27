#!/bin/bash
# Repository verification harness. Run from the repository root: ./scripts/verify.sh
# Requires: the project venv at ./venv (make setup) or VENV_PY pointing at a python
# with the [test] extras installed.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="${VENV_PY:-$REPO/venv/bin/python}"
PASS=0; FAIL=0
declare -a RESULTS

gate () {
  local name="$1"; shift
  if "$@" >/tmp/fcf_verify_out.txt 2>&1; then
    RESULTS+=("PASS  $name"); PASS=$((PASS+1))
  else
    RESULTS+=("FAIL  $name"); FAIL=$((FAIL+1))
    tail -6 /tmp/fcf_verify_out.txt | sed 's/^/       /'
  fi
}

echo "=== Future City Fellowship — repository verification ($(date)) ==="

gate "python: test suite with coverage gate (incl. legacy golden + cohort invariance + contract + offline GIS)" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/ -q --cov=fcf_m2 --cov-fail-under=80"

gate "python: legacy_v2 mode reproduces the accepted baseline (25 starter / 48 pathway)" \
  bash -c "cd '$REPO' && '$PY' -m fcf_m2.workflow run --mode legacy_v2 --out data/outputs/verify_legacy >/dev/null && grep -q '\"starter_total\": 25' data/outputs/verify_legacy/run_summary.json && grep -q '\"pathway_total\": 48' data/outputs/verify_legacy/run_summary.json"

gate "contract: tracked data/contract/v1 passes all rules + JSON Schema + RT-10 hash chain" \
  bash -c "cd '$REPO' && '$PY' -m fcf_m2.workflow validate-contract data/contract/v1"

gate "cross-model: MATLAB canonical CSV reconciles with the contract (ports, horizons, capacity_basis)" \
  "$PY" - <<EOF
import pandas as pd
from pathlib import Path
repo = Path("$REPO")
st = pd.read_csv(repo/"data/contract/v1/scenario_table.csv")
m = pd.read_csv(repo/"matlab/data/canonical/matlab_scenarios.csv")
assert set(st.horizon_year) == set(m.horizon_year) == {2026, 2036, 2046, 2056}
mg = st.merge(m, on="scenario_id"); assert len(mg) == len(st) == 120
assert (mg.ports_active == mg.ports).all()
assert mg.capacity_basis_y.notna().all()
print("cross-model OK")
EOF

gate "docs: generated workflow steps match the executable manifest" \
  bash -c "cd '$REPO' && '$PY' -c 'from fcf_m2 import workflow; d=open(\"docs/WORKFLOW_STEPS.md\").read(); assert f\"Step count: **{len(workflow.STEPS)}**\" in d'"

gate "dashboard: static assets present + every chart footer-logged" \
  bash -c "cd '$REPO' && [ \$(ls dashboard/static/0*.png | wc -l) -eq 9 ] && '$PY' -c \"
import sys; sys.path.insert(0,'src')
from fcf_m2.visuals import audit_footer_metadata
p = audit_footer_metadata('dashboard/static/footer_log.json','dashboard/static')
assert p == [], p\""

gate "secrets: no keys/tokens/account IDs in tracked files" \
  bash -c "cd '$REPO' && '$PY' scripts/secret_scan.py"

gate "hygiene: no local absolute paths in code/config" \
  bash -c "cd '$REPO' && ! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'"

gate "hygiene: no tracked file over 25 MB" \
  bash -c "cd '$REPO' && [ -z \"\$(git ls-files -z | xargs -0 -I{} find {} -size +25M 2>/dev/null)\" ]"

gate "links: markdown links resolve (lychee if installed, else internal-link check)" \
  bash -c "cd '$REPO' && if command -v lychee >/dev/null; then lychee --offline --no-progress README.md docs reports presentation dashboard excel matlab src tests scripts data 2>/dev/null; else '$PY' scripts/check_internal_links.py; fi"

echo
echo "=== RESULTS ==="
printf '%s\n' "${RESULTS[@]}"
echo "PASS: $PASS   FAIL: $FAIL"
[ "$FAIL" -eq 0 ] && echo "ALL REPOSITORY VERIFICATION GATES PASSED"
exit $FAIL
