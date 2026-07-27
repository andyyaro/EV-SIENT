function hexHash = fcf_sha256(filePath)
%FCF_SHA256 SHA-256 of a file. Replaces java.security.MessageDigest, which
%   needs a JVM (usejava("jvm") == 0 in this Octave build).
  fid = fopen(char(filePath), "r");
  if fid < 0; error("fcf_sha256:open", "Cannot open file: %s", char(filePath)); end
  bytes = fread(fid, Inf, "*uint8"); fclose(fid);
  hexHash = hash("sha256", char(bytes(:).'));
end
