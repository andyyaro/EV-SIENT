function opts = fcf_detectImportOptions(csvFile, varargin)
%FCF_DETECTIMPORTOPTIONS Minimal stand-in: reads the header line verbatim.
  fid = fopen(char(csvFile), "r");
  if fid < 0
    error("MATLAB:textio:textio:FileNotFound", "File not found: %s", char(csvFile));
  end
  hdr = fgetl(fid); fclose(fid);
  opts = struct();
  opts.VariableNames = strsplit(hdr, ",");
  opts.StringVars = {};
  opts.SourceFile = char(csvFile);
end
