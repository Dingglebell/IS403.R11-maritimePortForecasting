# Task 1 Data preparation and exploratory analysis

**Owners:** Nguyễn Thị Quỳnh Hân

**Stage:** 2 | **Handoff deadline:** 25 October 2026

Prepare a reliable daily port panel and explain how zero cargo days affect the study.

## Inputs

The downloaded PortWatch snapshot and the shared experiment protocol. Agree provisional time boundaries with Định and Hiếu before selecting ports.

## Work

1. Record source URL, download date, file hash, units and coverage. Recheck the reported 594,720 rows, 210 ports and 54.2% zero days; these are reference figures, not verified results for this checkout.
2. Check date and port keys, duplicate rows, missing calendar dates, missing values and negative values. Map source fields to the agreed schema. Compute cargo as import plus export.
3. Keep genuine zero cargo days. Do not turn missing records into zeros automatically. Investigate long zero runs, port calls on zero days and possible reporting gaps.
4. Select ports and define activity groups using training data only. Treat the earlier 20% active-day rule as a candidate; document retention by country.
5. Compare justified zero-handling or eligibility rules on validation with Task 2. Keep one common evaluation set and record exclusions. Plot cargo history, activity rates and cargo versus calls.

## Deliverables

| File or location | Expected output |
|---|---|
| `data/ports_daily.csv` | Clean panel plus dictionary and audit |
| `data/selected_ports.csv` | Port list and training-based groups |
| `results/data_audit.md` | Counts, zero-day analysis and figures |
| `docs/data_eda.md` | English Data and Exploratory Analysis |

## Completion check

One row per port and calendar date; missing and zero values are distinct. Every exclusion has a reason. Hand off the panel, metadata and frozen port rules to Task 2.

Suggested subroles and file paths are implementation proposals; owners and assignment deadlines follow the work plan. These are future deliverables, not files claimed to exist now.
