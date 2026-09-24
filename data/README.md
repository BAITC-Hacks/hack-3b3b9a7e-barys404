# Local data

Place source CSV files in this directory or in `raw/`. They are intentionally excluded from Git because they are large project data and may contain sensitive fields.

The loader detects datasets by their CSV columns and automatically combines newly added referral/refusal parts. Expected initial files are the waiting list, referral parts, refusal parts, and treated-case aggregate described in the project README.

Generated Parquet files and quality reports are written to `processed/` and are also excluded from Git. Each teammate must obtain the authorized source files through the team's approved data-sharing channel, then run:

```powershell
.\run.ps1
```

For the complete final-demo evidence, use `run.ps1 -Validate` before presenting. The interface lists every local CSV and marks files that are not connected to the hospital pipeline. Oncology and vaccination files are not model inputs. Laboratory research data (EIP) has not yet been provided; no laboratory forecast is claimed.
