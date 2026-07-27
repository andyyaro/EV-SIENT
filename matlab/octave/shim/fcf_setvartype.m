function opts = fcf_setvartype(opts, vars, typ)
%FCF_SETVARTYPE Records which columns must be text. Octave/datatypes readtable
%   already returns text columns as cellstr, so this is a recorder only.
  if ischar(vars); vars = {vars}; end
  opts.StringVars = vars;
end
