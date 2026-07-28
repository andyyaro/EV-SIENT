function n = fcf_strlength(s)
  if ischar(s); n = size(s, 2);
  elseif iscell(s); n = cellfun(@(v) size(char(v), 2), s);
  else; n = numel(char(s)); end
end
