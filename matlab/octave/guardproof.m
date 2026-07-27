more off;
pkg prefix /private/tmp/claude-501/-Users-andyyaro-Downloads-Future-City-Fellowship-MapUpdate/58698286-df36-4eee-8bc9-ff23a24df505/scratchpad/phase2/octave/pkg/prefix /private/tmp/claude-501/-Users-andyyaro-Downloads-Future-City-Fellowship-MapUpdate/58698286-df36-4eee-8bc9-ff23a24df505/scratchpad/phase2/octave/pkg/arch
pkg local_list /private/tmp/claude-501/-Users-andyyaro-Downloads-Future-City-Fellowship-MapUpdate/58698286-df36-4eee-8bc9-ff23a24df505/scratchpad/phase2/octave/pkg/octave_packages
pkg load datatypes
addpath('/private/tmp/claude-501/-Users-andyyaro-Downloads-Future-City-Fellowship-MapUpdate/58698286-df36-4eee-8bc9-ff23a24df505/scratchpad/phase2/octave/shim'); addpath('/private/tmp/claude-501/-Users-andyyaro-Downloads-Future-City-Fellowship-MapUpdate/58698286-df36-4eee-8bc9-ff23a24df505/scratchpad/phase2/octave/xform/src');
fail = 0;
function row = mkrow(basis)
  row = struct(); row.scenario_id = "T"; row.site_id = "S";
  row.capacity_basis = basis; row.service_capacity_kW = NaN;
  row.spare_capacity_kW = NaN; row.base_load_mean_kW = 50;
end
function [fired, id] = expect_error(f)
  fired = false; id = "";
  try; f(); catch e; fired = true; id = e.identifier; end
end
printf("=== G1: feasibility mode MUST error for every non-verified basis ===\n");
for b = {"placeholder","unknown","engineering_estimate","planning_proxy"}
  [fired,id] = expect_error(@() capacityGuard(mkrow(b{1}), "Mode", "feasibility"));
  ok = fired && strcmp(id, "capacityGuard:notVerified");
  printf("  %-22s fired=%d id=%-32s %s\n", b{1}, fired, id, merge(ok,"PASS","FAIL"));
  if !ok; fail++; end
end
printf("=== G2: default Mode (no argument) MUST fail closed ===\n");
[fired,id] = expect_error(@() capacityGuard(mkrow("placeholder")));
ok = fired && strcmp(id,"capacityGuard:notVerified");
printf("  default fired=%d id=%s %s\n", fired, id, merge(ok,"PASS","FAIL")); if !ok; fail++; end
printf("=== G3: out-of-vocabulary basis MUST error ===\n");
for b = {"confirmed_totally","verified","VERIFIED_UTILITY_X",""}
  [fired,id] = expect_error(@() capacityGuard(mkrow(b{1}), "Mode", "planning_illustration"));
  expected_ok = fired && strcmp(id,"capacityGuard:unknownBasis");
  if strcmp(b{1},""); expected_ok = !fired; end   % "" normalises to unknown, allowed in planning mode
  printf("  %-22s fired=%d id=%-32s %s\n", b{1}, fired, id, merge(expected_ok,"PASS","FAIL"));
  if !expected_ok; fail++; end
end
printf("=== G4: verified bases MUST pass feasibility and carry NO banner ===\n");
for b = {"verified_utility","verified_facility"}
  r = mkrow(b{1}); r.service_capacity_kW = 400;
  g = capacityGuard(r, "Mode", "feasibility");
  ok = (g.is_verified == true) && isscalar(g.is_verified) && (fcf_strlength(g.placeholder_banner) == 0) && (g.capacity_kW == 400);
  printf("  %-22s verified=%d scalar=%d bannerlen=%d cap=%g %s\n", b{1}, g.is_verified, isscalar(g.is_verified), fcf_strlength(g.placeholder_banner), g.capacity_kW, merge(ok,"PASS","FAIL"));
  if !ok; fail++; end
end
printf("=== G5: is_verified MUST be a SCALAR logical (the Octave defect signature) ===\n");
g = capacityGuard(mkrow("placeholder"), "Mode", "planning_illustration");
ok = islogical(g.is_verified) && isscalar(g.is_verified) && (g.is_verified == false);
printf("  class=%s size=%s value=%d %s\n", class(g.is_verified), mat2str(size(g.is_verified)), g.is_verified, merge(ok,"PASS","FAIL"));
if !ok; fail++; end
printf("=== G6: every non-verified guard MUST carry a non-empty banner ===\n");
for b = {"placeholder","unknown","engineering_estimate","planning_proxy"}
  g = capacityGuard(mkrow(b{1}), "Mode", "planning_illustration");
  ok = fcf_strlength(g.placeholder_banner) > 0;
  printf("  %-22s bannerlen=%d %s\n", b{1}, fcf_strlength(g.placeholder_banner), merge(ok,"PASS","FAIL"));
  if !ok; fail++; end
end
printf("=== G7: assumed capacity can NEVER upgrade provenance ===\n");
r = mkrow("verified_utility");
g = capacityGuard(r, "Mode", "planning_illustration", "AssumedSiteCapacity_kW", 200);
ok = (g.is_verified == false) && g.assumed_capacity_used && fcf_strlength(g.placeholder_banner) > 0;
printf("  verified=%d assumed=%d bannerlen=%d %s\n", g.is_verified, g.assumed_capacity_used, fcf_strlength(g.placeholder_banner), merge(ok,"PASS","FAIL"));
if !ok; fail++; end
printf("\n==== GUARD PROOF: %d failure(s) ====\n", fail);
if fail > 0; exit(1); end
