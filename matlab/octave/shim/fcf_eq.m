function tf = fcf_eq(a, b)
%FCF_EQ Octave stand-in for MATLAB string-array elementwise ==.
  if ischar(a) && ischar(b); tf = strcmp(a, b); return; end
  if iscell(a) || iscell(b)
    tf = strcmp(fcf_cellify(a), fcf_cellify(b));
    return;
  end
  tf = strcmp(char(a), char(b));
end
function c = fcf_cellify(x)
  if iscell(x); c = cellfun(@(v) char(v), x, "UniformOutput", false);
  elseif ischar(x); c = {x};
  else; c = {char(x)}; end
end
