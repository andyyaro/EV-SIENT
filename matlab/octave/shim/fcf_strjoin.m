function s = fcf_strjoin(c, delim)
  if nargin < 2; delim = " "; end
  if ischar(c); c = {c}; end
  if ~iscell(c); c = cellstr(c); end
  c = cellfun(@(v) char(v), c, "UniformOutput", false);
  s = strjoin(c, char(delim));
end
