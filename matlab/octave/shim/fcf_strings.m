function s = fcf_strings(varargin)
%FCF_STRINGS Octave stand-in for MATLAB strings(): cell array of ''.
  if nargin == 0; s = {""}; return; end
  if nargin == 1; sz = [varargin{1} varargin{1}]; else; sz = [varargin{:}]; end
  s = repmat({""}, sz);
end
