from datetime import date
import pytest
from pydantic import ValidationError
from src.models import AgentResponse, AssignmentItem, SyllabusChunk

def test_chunk_defaults_to_text():
    chunk = SyllabusChunk(text="Hello", course_code="CS 101", section_title="Intro",
                          page_number=1, source_file="cs101.pdf")
    assert chunk.chunk_type == "text"

def test_chunk_page_number_must_be_positive():
    with pytest.raises(ValidationError):
        SyllabusChunk(text="Hello", course_code="CS 101", section_title="Intro",
                      page_number=0, source_file="cs101.pdf")

def test_assignment_optional_fields():
    item = AssignmentItem(title="Homework 1", course_code="CS 101", page_reference=2)
    assert item.due_date is None and item.point_weight is None

def test_assignment_parses_date_string():
    item = AssignmentItem(title="Exam", course_code="CS 101", page_reference=2, due_date="2026-10-14")
    assert item.due_date == date(2026, 10, 14)

def test_agent_response_fields():
    r = AgentResponse(answer="10% per day", cited_quote="loses 10% per day", page_number=2)
    assert r.page_number == 2