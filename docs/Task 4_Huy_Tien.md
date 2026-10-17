# Task 4 Related work and optional forecasting extension

**Owners:** Trần Hoàng Huy, Lê Minh Tiến

**Stage:** 4 | **Handoff deadline:** 1 December 2026

Explain how the three studies inform this project and decide whether SARIMA or SARIMAX is feasible.

## Inputs

The supplied introductions, the three original papers listed in docs/references.md, the daily panel and any available oil-price series.

## Work

1. Write one short note per paper: question, data frequency, unit, methods, findings, limitation and what this group adopts. Verify citations against the originals before quoting results.
2. Suggested split: Huy leads the comparison and AIS studies; Tiến leads the SARIMAX study and oil data audit. Review and combine the notes.
3. Explain the differences between annual or monthly TEU, weekly commodity cargo and this project’s daily estimated tonnes. Do not claim to reproduce a study using a different target.
4. By the deadline, write a go or no-go decision based on coverage, frequency, publication timing, missing values, runtime and whether all core models are complete.
5. If feasible, fit per-port SARIMA on a training-selected subset, forecast seven daily values and sum them. For SARIMAX, use only oil values available at each forecast origin; future oil paths must be forecast or stated scenarios, never future observed prices.

## Deliverables

| File or location | Expected output |
|---|---|
| `docs/related_work.md` | English Related Work and adoption table |
| `docs/extension_decision.md` | Go or no-go with evidence |
| `src/sarimax.py` | Only if the extension proceeds |
| `results/extension_predictions.csv` | Only if feasible; identify the subset |

## Completion check

The no-go decision is a valid deliverable. If implemented, compare against core models on the same subset and origins. Monthly oil observations cannot be treated as known before their publication date.

Suggested subroles and file paths are implementation proposals; owners and assignment deadlines follow the work plan. These are future deliverables, not files claimed to exist now.
