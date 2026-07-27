function r = fcf_release()
%FCF_RELEASE Octave has no MATLAB release string. Returns an explicit marker
%   so provenance never silently claims a MATLAB release it did not run on.
  r = ["OCTAVE-" version() "-NOT-MATLAB"];
end
