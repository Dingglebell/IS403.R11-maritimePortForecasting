# Task 6 Research paper presentation and reproducibility

**Owners:** Nguyễn Thị Quỳnh Hân, Phạm Công Định, Lê Nguyễn Hữu Hiếu, Trần Hoàng Huy, Lê Minh Tiến

**Stage:** 6 | **Handoff deadline:** 27 December 2026

Deliver one coherent English research paper, a presentation of no more than 30 slides, and a reproducible repository.

## Inputs

Accepted outputs and English sections from Tasks 1 to 5, plus the paper and slide outlines in docs/.

## Work

1. Suggested integration roles: Hân checks data and charts; Định checks setup and reproducibility; Hiếu assembles slides; Huy integrates methods and discussion; Tiến checks citations and terminology. All five approve the final paper.
2. Merge the sections into the paper outline. Write the abstract and conclusion after results are fixed. Reconcile every number, unit, model name and citation across paper and slides.
3. Use Times New Roman 13, black text and gray table headers in documents. The final paper is English. Follow the 26-slide outline, leaving at most four extra slides including backup slides.
4. Run the final workflow from a fresh clone with the documented data snapshot and environment. Record exact package versions, commands, seeds and output locations.
5. Check that data access and license notes are clear, and that raw datasets and temporary files are excluded from Git. Resolve review comments and rehearse within the instructor’s presentation time.

## Deliverables

| File or location | Expected output |
|---|---|
| `docs/paper.docx` | Final English paper and submission export |
| `docs/slides.pptx` | Final presentation, at most 30 slides |
| `README.md` | Verified setup and execution commands |
| `requirements.txt` | Tested and pinned environment |
| `results/` | Final tables and figures |

## Completion check

Every member checks their section and another member’s section. One clean run reproduces the reported results. Confirm the submission format and presentation duration with the instructor before final export.

Suggested subroles and file paths are implementation proposals; owners and assignment deadlines follow the work plan. These are future deliverables, not files claimed to exist now.
