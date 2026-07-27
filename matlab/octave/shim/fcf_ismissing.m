function tf = fcf_ismissing(x)
  if ischar(x); tf = false;
  elseif iscell(x); tf = cellfun(@(v) (ischar(v) && isempty(v)) || (isnumeric(v) && isscalar(v) && isnan(v)), x);
  elseif isnumeric(x); tf = isnan(x);
  else; tf = false(size(x)); end
end
