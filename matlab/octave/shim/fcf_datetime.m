function s = fcf_datetime(varargin)
%FCF_DATETIME Minimal stand-in covering ONLY the "now"+TimeZone+Format use
%   in this repository. Returns a char timestamp, not a datetime object.
  fmt = "yyyy-mm-ddTHH:MM:SSZ";
  for i = 1:2:numel(varargin)
    if ischar(varargin{i}) && strcmpi(varargin{i}, "Format")
      f = char(varargin{i+1});
      f = strrep(f, "'", "");
      f = strrep(f, "yyyy", "yyyy"); f = strrep(f, "MM", "@MO@");
      f = strrep(f, "dd", "dd"); f = strrep(f, "HH", "HH");
      f = strrep(f, "mm", "MI"); f = strrep(f, "ss", "SS");
      f = strrep(f, "@MO@", "mm");
      f = strrep(f, "MI", "MM");
      fmt = f;
    end
  end
  s = datestr(now() - (java_tz_offset_hours() / 24), fmt);
end
function h = java_tz_offset_hours()
  h = (localtime(time()).gmtoff) / 3600;
end
