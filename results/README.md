# Experiment outputs

No model results exist yet. Save audit notes, predictions, configurations, metric tables and figures here as tasks are completed. Large outputs are ignored by default; explicitly add only reviewed small results, for example `git add -f results/metrics.csv`.

Use the prediction schema in docs/protocol.md. Store one row per model, feature set, split, port and origin. Keep validation outputs separate from the final test outputs. Record model settings, seeds, versions, dataset hash and the commit used for each run.

Suggested metric columns: model, feature_set, split, group_type, group_value, n_rows, n_ports, MAE, RMSE, WAPE_pct. Use NA for undefined WAPE. State units and sample counts on figures; export legible figures for the English paper and slides.
