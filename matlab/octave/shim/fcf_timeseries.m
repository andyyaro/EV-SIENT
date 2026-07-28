function ts = fcf_timeseries(data, t)
  ts = struct("Data", data, "Time", t, "note", "fcf shim: not a MATLAB timeseries");
end
