function T = fcf_readtable(csvFile, opts, varargin)
%FCF_READTABLE Wraps the Octave 'datatypes' readtable and RESTORES the exact
%   header names (MATLAB "VariableNamingRule","preserve" behaviour). The
%   datatypes reader mangles names such as 'case' -> 'xCase'.
  csvFile = char(csvFile);
  T = readtable(csvFile);
  fid = fopen(csvFile, "r"); hdr = fgetl(fid); fclose(fid);
  trueNames = strsplit(hdr, ",");
  got = T.Properties.VariableNames;
  if numel(trueNames) ~= numel(got)
    error("fcf_readtable:headerMismatch", ...
      "Header has %d names but the reader produced %d columns.", ...
      numel(trueNames), numel(got));
  end
  T.Properties.VariableNames = trueNames;
end
