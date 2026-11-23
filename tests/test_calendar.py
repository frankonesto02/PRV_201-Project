from datetime import date

import pytest

from src.calendar import export_calendar, read_assignments
from src.calendar.table_reader import parse_deadline
from src.ingestion import load_all, load_pdf
from src.models import AssignmentItem, SyllabusChunk


def table(text):
    return SyllabusChunk(text=text, course_code="CS 101", section_title="Deadlines",
                         page_number=2, source_file="cs101.pdf", chunk_type="table")


@pytest.mark.parametrize("text,expected_date,expected_time", [
    ("Fri, Sep 11 at 11:59 PM", date(2026, 9, 11), "23:59"),
    ("October 15", date(2026, 10, 15), None),
    ("2027-01-12 at 12:00 AM", date(2027, 1, 12), "00:00"),
    ("10/15/2027 at 12:30 PM", date(2027, 10, 15), "12:30"),
    ("Feb 29, 2028", date(2028, 2, 29), None),
])
def test_deadline_formats(text, expected_date, expected_time):
    assert parse_deadline(text, 2026) == (expected_date, expected_time)


@pytest.mark.parametrize("value", ["TBD", "next Friday", "Feb 30", "Sep 11 at 25:00"])
def test_uncertain_or_invalid_dates_are_not_guessed(value):
    with pytest.raises(ValueError):
        parse_deadline(value, 2026)


def test_reader_deduplicates_and_ignores_weekly_schedule():
    row = "Assignment: Homework 1 | Due Date: Sep 11 at 11:59 PM | Weight: 2.5%"
    items = read_assignments([table(row), table(row), table("Week: 1 | Week of: Sep 7 | Due this week: Homework 1")], year=2026)
    assert len(items) == 1
    assert items[0].due_date == date(2026, 9, 11)
    assert items[0].due_time == "23:59"
    assert items[0].point_weight == 2.5
    assert items[0].page_reference == 2


def test_unreadable_date_is_retained_for_review():
    with pytest.warns(UserWarning, match="page 2"):
        items = read_assignments([table("Assignment: Essay | Due Date: TBD")], year=2026)
    assert items[0].due_date is None


def test_export_handles_daylight_saving_and_date_only_events(tmp_path):
    items = [
        AssignmentItem(title="Summer", course_code="CS 101", page_reference=1, due_date="2026-09-11", due_time="23:59"),
        AssignmentItem(title="Winter", course_code="CS 101", page_reference=2, due_date="2026-12-08", due_time="09:00"),
        AssignmentItem(title="All day", course_code="CS 101", page_reference=2, due_date="2026-12-09"),
    ]
    output = tmp_path / "deadlines.ics"
    assert export_calendar(items, output) == 3
    content = output.read_text()
    assert "DTSTART:20260912T035900Z" in content
    assert "DTSTART:20261208T140000Z" in content
    assert "DTSTART;VALUE=DATE:20261209" in content
    uid_lines = [line for line in content.splitlines() if line.startswith("UID:")]
    export_calendar(items, output)
    assert uid_lines == [line for line in output.read_text().splitlines() if line.startswith("UID:")]


def test_export_escapes_text_folds_utf8_and_skips_undated(tmp_path):
    title = "Essay, notes; \\ practice\n" + "é" * 100
    items = [AssignmentItem(title=title, course_code="CS 101", page_reference=1, due_date="2026-09-11"),
             AssignmentItem(title="TBD", course_code="CS 101", page_reference=1)]
    path = tmp_path / "out.ics"
    with pytest.warns(UserWarning, match="Skipped undated"):
        assert export_calendar(items, path) == 1
    raw = path.read_bytes()
    assert all(len(line) <= 75 for line in raw.split(b"\r\n"))
    content = raw.decode().replace("\r\n ", "")
    assert "Essay\\, notes\\; \\\\ practice\\n" in content


@pytest.mark.parametrize("day,clock", [("2026-03-08", "02:30"), ("2026-11-01", "01:30")])
def test_clock_change_edge_cases_raise(tmp_path, day, clock):
    item = AssignmentItem(title="Exam", course_code="CS 101", page_reference=1, due_date=day, due_time=clock)
    with pytest.raises(ValueError, match="local time"):
        export_calendar([item], tmp_path / "out.ics")


def test_actual_cs101_pdf(tmp_path):
    items = read_assignments(load_pdf("data/syllabi/CS101_introduction-to-programming.pdf"), year=2026)
    assert len(items) == 9
    homework = next(item for item in items if item.title == "Homework 1")
    assert homework.due_date == date(2026, 9, 11)
    assert homework.due_time == "23:59"
    assert homework.page_reference == 1
    assert export_calendar(items, tmp_path / "cs101.ics") == 9


def test_all_sample_syllabi_produce_dated_assignments(tmp_path):
    chunks = load_all()
    expected = sum(row.startswith("Assignment:") and " | Due Date:" in row
                   for chunk in chunks if chunk.chunk_type == "table"
                   for row in chunk.text.splitlines())
    items = read_assignments(chunks, year=2026)
    assert len(items) == expected
    assert len({item.course_code for item in items}) == 10
    assert all(item.due_date and item.due_time for item in items)
    assert export_calendar(items, tmp_path / "all.ics") == expected
