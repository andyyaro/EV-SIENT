function tf = fcf_contains(str, pat, varargin)
  ic = false;
  for i = 1:2:numel(varargin)
    if strcmpi(varargin{i}, "IgnoreCase"); ic = logical(varargin{i+1}); end
  end
  if iscell(str)
    tf = cellfun(@(s) fcf_contains(s, pat, varargin{:}), str);
    return;
  end
  s = char(str); p = char(pat);
  if ic; s = lower(s); p = lower(p); end
  tf = ~isempty(strfind(s, p));
end
