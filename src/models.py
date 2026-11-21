from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class SyllabusChunk(BaseModel):
    """A quote from the syllabus and where it came from."""
    text: str
    course_code: str
    section_title: str
    page_number: int = Field(ge=1)
    source_file: str
    chunk_type: str = "text"

class AssignmentItem(BaseModel):
    """One assignment or exam or deadline."""
    title: str
    course_code: str
    due_date: Optional[date] = None
    due_time: Optional[str] = None        # "HH:MM", 24 hour clock
    point_weight: Optional[float] = None  # percent of final grade
    page_reference: int = Field(ge=1)


class AgentResponse(BaseModel):
    """Agent output: an answer plus proof from the syllabus."""
    answer: str
    cited_quote: str                      # exact words from the syllabus
    page_number: int = Field(ge=1)
