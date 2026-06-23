# Generated Outputs

This folder is for files created when the scripts run.

Generated CSV outputs:

```text
data/outputs/site_results.csv
data/outputs/data_quality_report.csv
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
```

Generated chart outputs:

```text
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/utilization_vs_ports_<site>.png
```

These generated outputs are ignored by Git so local runs do not clutter `git status`.

To regenerate them from the repository root:

```bash
python src/validate_site_data.py
python src/ev_charger_model.py
python src/run_sensitivity_analysis.py
```
