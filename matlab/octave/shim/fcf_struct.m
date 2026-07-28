function s = fcf_struct(varargin)
%FCF_STRUCT struct() with MATLAB string-array semantics: a cell value becomes
%   ONE field value (1x1 struct), not a struct array. Guards against the
%   cellstr-for-string-array transformation silently changing struct shape.
  args = varargin;
  for i = 2:2:numel(args)
    if iscell(args{i}); args{i} = args(i); end
  end
  s = struct(args{:});
end
