function s = fcf_str(x)
%FCF_STR Octave stand-in for MATLAB string(): returns char or cellstr.
  if ischar(x)
    s = x;
  elseif iscellstr(x)
    if isscalar(x); s = x{1}; else; s = x; end
  elseif iscell(x)
    s = cellfun(@(v) fcf_str(v), x, "UniformOutput", false);
  elseif islogical(x)
    if isscalar(x); if x; s = "true"; else; s = "false"; end
    else; s = arrayfun(@(v) fcf_str(v), x, "UniformOutput", false); end
  elseif isnumeric(x)
    if isscalar(x)
      if isnan(x); s = "NaN"; else; s = num2str(x, "%.15g"); end
    else
      s = arrayfun(@(v) fcf_str(v), x, "UniformOutput", false);
    end
  else
    s = char(x);
  end
end
