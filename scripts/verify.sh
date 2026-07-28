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

# v1 is frozen and v2 is additive. Both claims are load-bearing and neither is self-enforcing,
# so both are gated: the script rebuilds v2 from v1 into a temp dir and refuses if a fresh
# build differs from the tracked bytes or if any field shared with v1 changed value.
gate "contract: v2 rebuilds byte-identically from the frozen v1 and every shared field is unchanged" \
  bash -c "cd '$REPO' && '$PY' scripts/build_contract_v2.py --check"

gate "contract: tracked data/contract/v2 passes v1 rules + v2 rules + JSON Schema + RT-10 hash chain" \
  bash -c "cd '$REPO' && '$PY' -m fcf_m2.workflow validate-contract data/contract/v2"

# A physical assumption may not hold two values in two halves of one model. charger
# efficiency was 0.92 in Python and 0.93 in three MATLAB files, and survived because it is
# not a contract field -- so there was nothing to reconcile it against.
gate "cross-model: shared physical constants agree between Python and MATLAB" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_cross_model_constants.py -q"

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

# Gated on the .twb, NEVER the .twbx digest. Measured: two consecutive builds from a
# byte-identical spec give an identical .twb and DIFFERENT .twbx digests, because the
# embedded Hyper extracts carry non-deterministic engine state. A package-digest gate would
# fail on every run and be deleted within a week, taking the real check with it.
# The platform's central promise: no number appears without its provenance available. This
# also enforces STRICT JSON on the web-tier export -- numpy NaN wrote 281 bare `NaN` literals
# that Python reads back happily and a browser rejects outright.
# An operation IS the CLI command, not a second code path -- which is what makes Gate 7's
# byte-equivalence a property of the design. Also enforces that the web tier lists every
# capability with a stated reason where it cannot run one, rather than hiding it.
# A local server that can execute commands is reachable by ANY page in your browser --
# loopback is not a boundary against that. The token is what closes it, so the token
# behaviour is tested harder than the features.
# Never conflate engines; surface divergences rather than hiding them. Every figure in the
# record is read out of a committed CI artifact, so this also fails if those go missing.
# DEC-016: the real site inputs never reach the public bundle. By construction, not by
# convention -- a convention is something a later change breaches without noticing.
# Gate 7: platform output byte-identical to CLI output. Proven over PRODUCED FILES, not
# just stdout -- if the two paths ever wrote different bytes the disagreement would surface
# as an inexplicable number rather than as an error.
# A block diagram is the kind of artifact a reader assumes produced something. This one did
# not -- built once, never simulated -- and the view must say so alongside the topology.
gate "platform: Simulink view matches the real .slx and states it was never simulated" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_simulink_view.py -q"

gate "platform: generated artifacts are byte-identical via the platform and via the CLI" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_cli_platform_equivalence.py -q"

gate "platform: public bundle matches its manifest and excludes the real site inputs" \
  bash -c "cd '$REPO' && '$PY' scripts/build_platform_surfaces.py >/dev/null && '$PY' -m pytest tests/test_platform_surfaces.py -q"

gate "platform: engines are distinguishable and every divergence is surfaced" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_engine_record.py -q"

gate "platform: local server binds loopback, requires a token, runs only declared operations" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_server.py -q"

gate "platform: web tier is wired to what exists, computes nothing, keeps its caveats" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_platform_web.py -q && '$PY' scripts/build_platform_web.py --check"

gate "platform: operations match the CLI byte-for-byte; web tier states what it cannot do" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_operations.py -q"

gate "platform: every displayed number resolves to its lineage; both tiers agree" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_provenance.py -q"

gate "tableau: workbook data matches the contract; .twb declares its sheets and caveats" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_tableau_workbook.py -q"

# Two Tableau URL forms exist and are not interchangeable. Both return 200 and the same
# ~1.4 KB JS shell, so nothing about a status check catches the wrong one -- and an embed
# built on the page form fails looking like a rendering problem rather than a bad URL.
gate "tableau: embeds use the /views/ share form, never the profile page form" \
  bash -c "cd '$REPO' && '$PY' scripts/check_tableau_embeds.py"

gate "secrets: no keys/tokens/account IDs in tracked files" \
  bash -c "cd '$REPO' && '$PY' scripts/secret_scan.py"

# Widened on BOTH axes after a tracked .m file was found hardcoding one session's temporary
# scratchpad directory. The gate searched five extensions for a single home-directory prefix;
# the offending file was a sixth extension carrying a different prefix, so it passed a check
# whose name claims "no local absolute paths in code/config". A gate that names a class and
# tests one member of it is worse than one with a stated hole, because nobody looks for the
# hole.
gate "hygiene: no machine-specific absolute paths in tracked source" \
  bash -c "cd '$REPO' && ! git grep -nIE '(/Users/[a-z]+|/home/[a-z]+|/private/tmp/claude|/tmp/claude-[0-9])' -- '*.py' '*.sh' '*.m' '*.toml' '*.yml' '*.yaml' '*.json' '*.js' '*.mjs' ':!scripts/verify.sh'"

gate "hygiene: no tracked file over 25 MB" \
  bash -c "cd '$REPO' && [ -z \"\$(git ls-files -z | xargs -0 -I{} find {} -size +25M 2>/dev/null)\" ]"

gate "3d: explorer suite passes (attribution reproduces the model score in BOTH modes)" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_explorer_pipeline.py tests/test_explorer_drift.py -q"

gate "3d: sites.geojson is strict-valid RFC 7946 with the 12 expected sites in Northern Virginia" \
  "$PY" - <<EOF
import json
from pathlib import Path
repo = Path("$REPO")
fc = json.loads((repo / "explorer/web/data/sites.geojson").read_text())
assert fc["type"] == "FeatureCollection", fc.get("type")
feats = fc["features"]
assert len(feats) == 12, len(feats)
ids = sorted(f["properties"]["site_id"] for f in feats)
expected = sorted([f"FFX{n:03d}" for n in range(1, 5)] + [f"PWC{n:03d}" for n in range(1, 9)])
assert ids == expected, ids
for f in feats:
    assert f["type"] == "Feature" and f["geometry"]["type"] == "Point"
    lon, lat = f["geometry"]["coordinates"][:2]
    assert -77.8 <= lon <= -77.0 and 38.5 <= lat <= 39.1, (f["properties"]["site_id"], lon, lat)
blob = json.dumps(fc)
for retired in ("ports_2035", "ports_2050"):
    assert retired not in blob, f"committed payload carries the retired field {retired}"
man = json.loads((repo / "explorer/web/data/manifest.json").read_text())
assert man["mode"] == "milestone2_v3" and man["mode_is_canonical"] is True, man["mode"]
print("3D payload OK: 12 sites, RFC 7946, canonical horizons only")
EOF

gate "3d: all 12 GLB models are well-formed glTF 2.0" \
  "$PY" - <<EOF
import json, struct
from pathlib import Path
d = Path("$REPO") / "explorer/web/models"
globs = sorted(d.glob("*.glb"))
assert len(globs) == 12, f"expected 12 GLB models, found {len(globs)}"
for p in globs:
    raw = p.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF", (p.name, magic)
    assert version == 2, (p.name, version)
    assert length == len(raw), (p.name, length, len(raw))
    clen, ctype = struct.unpack_from("<II", raw, 12)
    assert ctype == 0x4E4F534A, (p.name, hex(ctype))
    json.loads(raw[20:20 + clen].decode("utf-8"))
print(f"all {len(globs)} GLB models are well-formed glTF 2.0")
EOF

gate "3d: viewer JS parses and every CDN reference is version-pinned" \
  bash -c "cd '$REPO' && { command -v node >/dev/null && node --check explorer/web/app.js || echo 'node absent - JS syntax check skipped'; } && '$PY' scripts/check_cdn_pins.py"

gate "matlab: nothing destined for the PUBLIC harness carries site-identifying data" \
  bash -c "cd '$REPO' && '$PY' scripts/check_harness_exposure.py"

# The field-entry form must never accept an observation the model will refuse — otherwise a
# field worker is told a record was saved when it was not. The schema is generated from
# observed.py and this gate runs the same candidate rows through the browser validator and the
# real CSV readers. It has already earned its place: it found blank attribution surviving as
# the string "nan", which let an unattributed row claim verified_utility.
gate "field-entry: the browser's rules never accept what the model rejects" \
  bash -c "cd '$REPO' && '$PY' scripts/build_field_schema.py >/dev/null && '$PY' -m pytest tests/test_field_schema_parity.py -q"

# The desktop tier's entry point. Before it existed the documented command was
# `python -m fcf_m2.server`, which fails with a bare traceback if the bundle was never built --
# an error naming a missing directory rather than the step the reader skipped.
gate "platform: the desktop launcher builds what is derivable and refuses what is not" \
  bash -c "cd '$REPO' && '$PY' -m pytest tests/test_launcher.py -q && '$PY' -m fcf_m2.launcher --check"

# Every link the platform offers must resolve to a real file, resolved the way S3 resolves it
# (a trailing slash means index.html, nothing is generated on demand). Five surfaces linked to
# directories that do not exist as objects; it passed locally because Python's http.server
# generates directory listings and S3 does not. The local server was more capable than
# production and hid the defect.
gate "platform: every surface link resolves to a file that exists in the bundle" \
  bash -c "cd '$REPO' && '$PY' scripts/check_surface_links.py"

# A public installer ships invented inputs (DEC-016). This gate checks the synthetic set is
# usable, honest, and NOT a disguised copy — including the subtle failure, where a fixture
# produced by perturbing real values preserves the rank order and re-identifies sites anyway.
# It also builds the public artifact and INSPECTS IT, because an artifact whose inputs were
# correctly substituted still shipped 36 real facility identifiers through files nobody had
# thought of.
gate "synthetic: the public input set is usable, honest, and not a disguised copy" \
  bash -c "cd '$REPO' && '$PY' scripts/build_synthetic_inputs.py >/dev/null && '$PY' -m pytest tests/test_synthetic_inputs.py -q && '$PY' scripts/build_release_artifact.py /tmp/fcf_public_gate --public >/dev/null && rm -rf /tmp/fcf_public_gate"

# The public website must carry its own caveats and must not embed a workbook that no longer
# exists. The patch package sat unapplied for three weeks; the Tableau embeds pointed at a
# workbook that had been deleted, so every one resolved to resource-not-found.
gate "website: public pages carry their caveats and embed only the canonical workbook" \
  bash -c "cd '$REPO' && '$PY' scripts/patch_site_www.py >/dev/null && '$PY' scripts/retarget_tableau_embeds.py >/dev/null && '$PY' scripts/check_site_www.py"

# Drives the entry form in a real headless Chrome — the only check that sees what a person
# sees. It exists because this program has twice shipped a feature that passed every test and
# was unusable: two blank Tableau sheets, and a sign-in page that did not exist. Both times the
# check verified the step under our control rather than the outcome the reader experiences.
# Skips loudly (not silently) when Chrome is absent, so CI without a browser stays green.
gate "field-entry: the form refuses and accepts VISIBLY in a real browser" \
  bash -c "cd '$REPO' && if ! command -v node >/dev/null; then echo 'node absent - browser test SKIPPED'; exit 0; fi; \
    '$PY' -m fcf_m2.server --port 8799 >/tmp/fcf_gate_server.log 2>&1 & SRV=\$!; \
    trap 'kill \$SRV 2>/dev/null' EXIT; \
    for i in \$(seq 1 30); do curl -sf -o /dev/null http://127.0.0.1:8799/index.html && break; sleep 0.5; done; \
    node --test 'tests/browser/*.test.mjs'"

# The edge authoriser is the only thing standing between an anonymous request and the study's
# full lineage, so its tests run here rather than only in the deploy path. They exercise the
# REAL handler with REAL RSA keys — only the network is stubbed — so a regression in token
# verification fails the repository gates, not just a deployment nobody re-ran.
gate "edge-auth: only a verified id_token for the granted account reaches the origin" \
  bash -c "cd '$REPO' && if command -v node >/dev/null; then node --test 'tests/edge_auth/*.test.mjs'; else echo 'node absent - edge auth tests SKIPPED (deploy path still runs them)'; fi"

gate "links: markdown links resolve (lychee if installed, else internal-link check)" \
  bash -c "cd '$REPO' && if command -v lychee >/dev/null; then lychee --offline --no-progress README.md docs reports presentation dashboard excel matlab src tests scripts data 2>/dev/null; else '$PY' scripts/check_internal_links.py; fi"

echo
echo "=== RESULTS ==="
printf '%s\n' "${RESULTS[@]}"
echo "PASS: $PASS   FAIL: $FAIL"
[ "$FAIL" -eq 0 ] && echo "ALL REPOSITORY VERIFICATION GATES PASSED"
exit $FAIL
