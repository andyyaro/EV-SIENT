% Guard proof: capacityGuard must refuse every non-verified capacity basis.
%
% Paths are resolved RELATIVE to this file. They were absolute when this was committed --
% baked into one session's temporary scratchpad, so the script could not run on any other
% machine, or on this one once that directory was cleaned up. The repository's hygiene gate
% did not catch it: the gate searched five source extensions for one home-directory prefix,
% and this is a .m file that carried a different prefix entirely. Its name promised more
% than it checked; the gate has since been widened on both axes.
%
% Run with:  octave --no-gui matlab/octave/guardproof.m
%
% THE TRANSFORM IS NOT OPTIONAL, and this script used to skip it. It added
% `matlab/src` -- the UNTRANSFORMED MATLAB sources -- directly to the path, and the
% documented one-line invocation above therefore could not pass. Measured: every G1-G3
% check reported FAIL because Octave raises those errors with an EMPTY identifier from
% untransformed source, so `capacityGuard:notVerified` never matched, and G4 died outright
% inside inputParser validation. Against a transformed tree the same script reports
% 0 failures. The guard was fine; the invocation was not.
%
% So the transform now runs here, into a temporary directory, and THAT is what goes on the
% path. The one-liner above is true again.
more off;

here = fileparts(mfilename("fullpath"));
addpath(fullfile(here, "shim"));

repo = fullfile(here, "..", "..");
xf = fullfile(tempdir(), sprintf("fcf_octave_src_%d", getpid()));
mkdir(xf); mkdir(fullfile(xf, "src")); mkdir(fullfile(xf, "tests"));

py = fullfile(repo, "venv", "bin", "python");
if ~exist(py, "file"); py = "python3"; end
cmd = sprintf('"%s" "%s" "%s" "%s"', py, fullfile(here, "transform.py"), ...
              fullfile(repo, "matlab"), xf);
[rc, out] = system(cmd);
if rc != 0
  printf("FATAL: MATLAB->Octave transform failed (exit %d). This proof cannot run against\n", rc);
  printf("       untransformed sources -- see the note at the top of this file.\n%s\n", out);
  exit(2);
end
addpath(fullfile(xf, "src"));
printf("(transformed sources into %s)\n", xf);

% Octave's `datatypes` package supplies struct helpers the shim relies on. Loaded only if
% present, so the script still runs where it is unavailable and says what it could not load.
try
  pkg load datatypes;
catch
  printf("note: Octave package 'datatypes' not loaded; shim fallbacks will be used\n");
end

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
