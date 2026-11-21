from pathlib import Path
import pytest
from src.ingestion import load_all, load_pdf
from src.ingestion.pdf_loader import find_course_code, looks_like_heading

SYLLABI = Path("data/syllabi")
CS101 = SYLLABI / "CS101_introduction-to-programming.pdf"

def test_ten_sample_syllabi_exist():
    assert len(list(SYLLABI.glob("*.pdf"))) == 10

def test_load_pdf_returns_chunks_with_valid_pages():
    chunks = load_pdf(CS101)
    assert len(chunks) > 5
    assert all(1 <= c.page_number <= 3 for c in chunks)
    assert all(c.source_file == CS101.name for c in chunks)

def test_late_policy_is_on_page_2_with_right_section():
    chunks = load_pdf(CS101)
    late = [c for c in chunks if "10% per day" in c.text]
    assert len(late) == 1
    assert late[0].page_number == 2
    assert late[0].section_title == "Late Work Policy"

def test_tables_become_table_chunks():
    tables = [c for c in load_pdf(CS101) if c.chunk_type == "table"]
    assert any("Weight:" in c.text for c in tables)
    assert any("Homework 1" in c.text and "Sep 11" in c.text for c in tables)

def test_table_text_is_not_also_in_text_chunks():
    text_chunks = [c for c in load_pdf(CS101) if c.chunk_type == "text"]
    assert not any("Week of" in c.text for c in text_chunks)

def test_headers_and_footers_are_removed():
    for c in load_pdf(CS101):
        assert "Course Syllabus" not in c.text
        assert "Page 2" not in c.text

def test_all_ten_course_codes_detected():
    codes = {c.course_code for c in load_all()}
    assert len(codes) == 10
    assert "UNKNOWN" not in codes

def test_two_column_syllabus_keeps_sentences_whole():
    chunks = load_pdf(SYLLABI / "BIO150_general-biology-i.pdf")
    assert any("Laboratory attendance is mandatory" in c.text and
               c.text.count("for that lab.") == 1 for c in chunks)

def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_pdf("data/syllabi/does_not_exist.pdf")

@pytest.mark.parametrize("text,filename,expected", [
    ("CS 101: Intro", "x.pdf", "CS 101"),
    ("MATH-221 Calculus", "x.pdf", "MATH 221"),
    ("Welcome to class", "bio150_notes.pdf", "BIO 150"),
    ("Welcome to class", "notes.pdf", "UNKNOWN"),
])
def test_find_course_code(text, filename, expected):
    assert find_course_code(text, filename) == expected

@pytest.mark.parametrize("line,expected", [
    ("Late Work Policy", True),
    ("Assignments and Due Dates", True),
    ("3. COURSE DESCRIPTION", True),
    ("Late homework loses 10% per day.", False),
    ("Instructor: Dr. Raman", False),
    ("The required text is a book", False),
])
def test_looks_like_heading(line, expected):
    assert looks_like_heading(line) == expected
