# Deadline reader and calendar export

This component takes table chunks from the existing PDF loader, creates the
team's `AssignmentItem` objects, and exports dated items to an `.ics` file.
It runs independently of the retrieval/LLM components and needs no Gemini key.

## Run from the project root

Install dependencies using the main README first. For this component alone:

```bash
python -m pip install pymupdf pdfplumber pydantic tzdata pytest
python -m src.calendar --year 2026
```

That processes the ten sample PDFs in `data/syllabi/` and writes:

- `data/calendar/deadlines.ics`: calendar events ready for import.
- `data/calendar/deadlines.json`: extracted assignments, dates, times, weights,
  and page references for review before importing.

For one course:

```bash
python -m src.calendar --input data/syllabi/CS101_introduction-to-programming.pdf --year 2026 --output data/calendar/cs101.ics
```

For a different timezone, supply `--timezone Europe/London`, for example.
The default is `America/New_York`. Times are converted to UTC with daylight
saving accounted for; dates without times become all-day events.

## How the code works with others

- `table_reader.py`: reads `Assignment`, `Due Date`, and optional `Weight`
  fields from the loader's table rows. Grading breakdowns and weekly schedules
  are ignored because they do not specify exact assignment deadlines.
- `ics_exporter.py`: creates calendar events with course/name, deadline, source
  page, and grade weight. Includes text escaping and UTF-8 line folding.
- `__main__.py`: connects ingestion, deadline reading, JSON review, and export.
- `tests/test_calendar.py`: checks parsing, invalid dates, duplicate rows,
  timezone handling, file formatting, and integration with the sample PDFs.

Example for another team component:

```python
from src.ingestion import load_pdf
from src.calendar import read_assignments, export_calendar

chunks = load_pdf("data/syllabi/CS101_introduction-to-programming.pdf")
items = read_assignments(chunks, year=2026)
export_calendar(items, "data/calendar/cs101.ics")
```

## Limits

This is a deterministic table reader, not the project's AI question-answering
agent. It currently supports the column labels and table-row format above.
Supported dates include `Sep 11`, `September 11`, `2026-09-11`, and US
month/day slash dates, optionally followed by `at 11:59 PM` or `at 23:59`.
Printed years take precedence; `--year` fills in missing years. A fall-to-spring
syllabus without printed years needs manual review because there is no automatic
term/year inference. Non-English dates and relative dates are not supported.

Unrecognized or invalid deadlines such as `TBD` remain in the JSON with no date,
produce a warning, and are excluded from calendar export. Ambiguous/nonexistent
times at daylight-saving transitions raise an error for manual correction.
Duplicate rows within a source PDF are removed; different PDF versions are not
reconciled. Stable calendar UIDs are supplied, but repeated imports may still
create duplicates depending on the calendar app. This exports a file; it does
not sync calendars, detect syllabus updates, or send notifications.

To test:

```bash
python -m pytest
```
