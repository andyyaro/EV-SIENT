function s = fcf_cat(varargin)
%FCF_CAT Octave stand-in for MATLAB string "+" concatenation.
  parts = cell(1, nargin);
  for i = 1:nargin
    v = varargin{i};
    if ischar(v); parts{i} = v;
    elseif iscellstr(v) && isscalar(v); parts{i} = v{1};
    else; parts{i} = fcf_str(v); end
    if ~ischar(parts{i}); parts{i} = char(parts{i}); end
  end
  s = [parts{:}];
end
