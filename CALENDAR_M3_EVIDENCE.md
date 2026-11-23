# Calendar working

Dylan's deadline table reader and calendar export.

## results

- `python -m src.calendar --year 2026` processed the ten sample syllabus PDFs.
- Found 95 assignments and exported 95 calendar events.
- Generated `data/calendar/deadlines.ics` and `data/calendar/deadlines.json`.
- `python -m pytest -q`: 41 tests passed (one unrelated installed pytest-plugin deprecation warning).
- A separate check using the independent `icalendar` parser successfully parsed
  all 95 events, checked their titles, and verified their dates in New York time.
  This parser was used for validation only; the exporter needs no such dependency.
- A calendar application's import screen has not been tested.

## Extracted counts

| Course | Events |
|---|---:|
| BIO 150 | 14 |
| CHEM 111 | 10 |
| CS 101 | 9 |
| ECON 201 | 8 |
| ENG 110 | 11 |
| HIST 205 | 5 |
| MATH 221 | 8 |
| PHYS 201 | 12 |
| PSYC 101 | 9 |
| STAT 301 | 9 |

## How to demonstrate

Run the command above from the project root. Compare the first CS 101 homework
in the syllabus with its JSON entry: September 11, 2026 at 23:59, syllabus page 1.
The calendar stores that instant as September 12 at 03:59 UTC, which displays
as September 11 at 23:59 in America/New_York. The files cover sample data;
review them before importing.

This validates the calendar component and existing ingestion/model tests.
The retrieval and AI question-answering components still need separate work.
